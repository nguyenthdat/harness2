---
name: ioc-extraction
description: Read when extracting C2, hosts, mutexes, paths, registry keys, or other indicators. Defines which values are indicators and which stay hypotheses.
---

# IOC extraction

An indicator is a value the bytes contain and reachable code uses, or the sample's own hash.

Record, with offset and the instruction or decode that produced them:

- SHA-256 of the sample and of an extracted payload you actually wrote to disk.
- A decoded URL, host, IP, or `host:port` that a connect, resolve, or HTTP path consumes.
- A mutex, file path, registry key, pipe, service name, or user-agent stored as data and referenced by code.

Do not record:

- A hex blob, an undecoded buffer, or a description of an endpoint. Those are not C2.
- A host that appears only in a compiler, library, or certificate URL.
- A domain guessed from a cipher, a DGA hypothesis, or a family name.
- A protocol from `socket` alone. Name the protocol only when the bytes show the message that is sent.

If no endpoint decodes, say that C2 was not recovered and list the scans. Static analysis cannot show that an endpoint was contacted.
