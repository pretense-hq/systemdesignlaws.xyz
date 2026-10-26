# Consistent Hashing

**TL;DR** - Modulo hashing reshuffles almost every key when the cluster size changes. Consistent hashing puts nodes and keys on a ring so a membership change moves about 1/N of the keys. Add virtual nodes for even load, walk the ring for replicas, and remember it balances keys; traffic needs its own fix.

>> 30-second elevator pitch: "I map keys and servers onto the same hash ring. A key belongs to the first server clockwise from it. When a server joins or dies, one slice of the ring changes owner. Each server gets many virtual positions, so load stays even and a failure spreads evenly across all survivors."

---

## Why Modulo Hashing Reshuffles on Resize

You run a cache tier with 4 servers and route with server = hash(key) mod 4. It is fast, stateless, and even. Then you add a fifth server.

Under hash(key) mod 5, a key stays put exactly when its hash leaves the same remainder under both divisors. For uniform hashes that happens with probability 1/(N+1), so going from 4 to 5 servers keeps 20 percent of keys and moves 80 percent. In general, adding one node to N moves N/(N+1) of all keys.

For a cache, that is a miss storm that dumps reads onto the database. For a sharded database, it means copying most of the dataset to add capacity.

<!-- DIAGRAM: hash mod 4 vs hash mod 5, showing most keys landing on a different server after adding one node -->

---

## What Is Consistent Hashing?

**Consistent hashing** is a placement scheme where adding or removing one node relocates just the keys that node gains or loses, roughly 1/N of the total.

### The Ring

Take a hash function with a large output range, such as 0 to 2^32 - 1, and wrap it into a circle. Hash each server's identifier to get its position. Hash each key with the same function to get the key's position.

### Lookup: Walk Clockwise

A key belongs to the first server clockwise from its position, so each server owns the arc between its predecessor and itself. In practice this is a sorted array of server positions and a binary search for the first position at or after the key's hash, wrapping to the start.

<!-- DIAGRAM: hash ring with servers A, B, C and keys k1 to k4, arrows showing each key moving clockwise to its owner -->

### What Moves on a Join or Leave

When server D joins between A and B, it takes the keys on the arc from A to D, which used to belong to B. Every other arc keeps its owner. If D later fails, that arc falls back to B.

With N evenly loaded nodes, a join moves about 1/(N+1) of the keys and a removal about 1/N. Going from 4 to 5 servers now moves roughly 20 percent, down from 80.

<!-- DIAGRAM: ring before and after server D joins, highlighting the single arc that changes owner from B to D -->

{{PAYWALL}}

---

## Virtual Nodes

### Why Each Server Needs More Than One Point

Random positions split a circle unevenly. With N random points, the expected largest arc is (1 + 1/2 + ... + 1/N) / N of the ring. For N = 10 that sum is about 2.93, so the unluckiest server owns close to 3x its fair share. Failure makes it worse: a dead node's whole arc lands on one successor, which can double that server's load at once.

### How Virtual Nodes Fix It

A **virtual node** is one of many positions a physical server occupies on the ring. In place of hashing "server-A" once, you hash "server-A#0" through "server-A#199". The physical server owns the sum of its small arcs.

### The Math to Quote

With N servers and V virtual nodes each, the expected share per server is still 1/N; V changes just the spread, and the average stays put. A server's share is the sum of V small, roughly independent arcs, so its deviation from 1/N shrinks roughly as 1/sqrt(V). At V = 100 a typical server is within about 10 percent of average; at V = 1,000, about 3 percent.

Failures spread too. A dead server's virtual nodes are scattered, so its keys flow to many successors, and each of the N - 1 survivors grows from 1/N to about 1/(N-1) of the keys.

The cost is small. Lookup is a binary search over N x V positions: 50 servers with 200 virtual nodes each is 10,000 entries, about 14 comparisons.

### Weighting Uneven Hardware

Give a server with twice the memory twice the virtual nodes and it gets about twice the keys. Drain a node gradually by removing its virtual nodes in batches.

<!-- DIAGRAM: three physical servers with interleaved colored virtual nodes around the ring, next to a ring of three single points with one oversized arc -->

---

## Replication on the Ring

To store each key on R servers, find the owner and keep walking clockwise until you have R distinct physical servers. Skip positions belonging to a server already chosen, since adjacent virtual nodes often map to the same machine. A zone-aware walk also skips zones already used, so one zone outage costs at most one copy.

This ordered candidate list is the **preference list**. Quorum rules, such as write to 2 of 3 and read from 2 of 3, sit on top of it.

<!-- DIAGRAM: key on the ring, clockwise walk selecting three distinct servers in different zones, skipping a duplicate virtual node -->

---

## Operating It

### Who Holds the Ring?

Every router must agree on membership, or two clients will send one key to different servers. A coordination service such as ZooKeeper or etcd can hold the list, nodes can gossip it, or a proxy layer can own routing.

### Moving the Data

The ring says who owns a key; getting the data there is a separate job. A cache can let moved keys miss and refill. A database must stream the arc to the new owner first, or read from the previous owner until the copy completes.

### Hot Keys Still Hurt

Consistent hashing balances key counts; request rates need a separate fix. One celebrity key still maps to one owner. Cache it in-process at the app tier, or split it into suffixed copies (key#1 to key#8) spread around the ring and read a random one.

---

## Alternatives Worth Naming

- **Fixed hash slots** - Hash keys into a fixed slot count, such as 16,384 in Redis Cluster, and assign slots to nodes. Pros: explicit, observable rebalancing. Cons: slot count caps how finely you can split.
- **Rendezvous hashing** - Score every node with hash(key, node) and pick the highest. Pros: minimal movement, just a node list to maintain. Cons: O(N) work per lookup.
- **Jump consistent hash** - Computes a bucket number purely from the key and the bucket count. Pros: even balance, zero memory. Cons: buckets are numbered, so you add or remove at the end.
- **Bounded loads** - Cap each node at (1 + epsilon) times the average and push overflow clockwise. Pros: limits skew. Cons: extra bookkeeping.

<!-- DIAGRAM: side-by-side of a ring with virtual nodes, a fixed slot table, and rendezvous scoring for one key -->

---

## When to Use in Interviews

Reach for it in a distributed cache, a key-value store, sticky load balancing, or a chat service that pins each room to one server. Skip it when the node count is small and fixed, or a managed database already partitions for you.

---

## Summary

- **Ring over modulo** - About 1/N of keys move per change, compared with N/(N+1).
- **Virtual nodes** - Share stays 1/N, spread shrinks as 1/sqrt(V).
- **Limits** - Hot keys need their own fix; membership must be agreed on.

Practice consistent hashing by designing a distributed cache or key-value store and tracing exactly which keys move when a node joins and when one fails.

## Interview Q&A

- **Why the ring over hash mod N?** - Changing N remaps N/(N+1) of keys, emptying a cache or forcing a near-full reshuffle. The ring moves about 1/N.
- **How many virtual nodes?** - A few hundred per server. Spread scales as 1/sqrt(V), so 100 to 200 gives roughly 7 to 10 percent deviation at trivial lookup cost.
- **What happens when a node fails?** - Its arcs pass clockwise, spread across survivors by virtual nodes; replicas already hold the data.
- **Does it solve hot keys?** - It balances keys, so hot keys need their own fix: an in-process cache or split copies.
- **How do clients learn about changes?** - From a coordination service, gossip, or a routing proxy. Version the ring so stale clients can detect it.
- **Ring or fixed slots?** - Slots make rebalancing explicit; a ring with virtual nodes lets you skip choosing a slot count upfront. Either works if you state the trade-off.

{{SUBSCRIBE}}

{{BUTTON:Read More Articles|https://newsletter.systemdesignlaws.xyz}}
