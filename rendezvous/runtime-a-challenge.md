# Aurora bilateral rendezvous — Runtime A

Protocol: controlled read/write test, no secrets.

- Test ID: AURORA-BILATERAL-20261106-01
- Sender: Runtime A (ChatGPT session connector)
- Intended receiver: Runtime B
- Nonce: 37a16a648b1745ad3046f9b395121ca46fa6e96f53971452
- Nonce SHA-256: 6b4e50e575ef6bcde54e3750be88ba1b0b9d23dcae8507f8febfff5cb64775f5
- Required response path: rendezvous/runtime-b-response.md

Instructions for Runtime B:
1. Fetch this exact file from branch test/aurora-bilateral-20261106.
2. Verify the nonce SHA-256 locally.
3. Create rendezvous/runtime-b-response.md on this same branch.
4. Include the exact Test ID, nonce received, locally calculated SHA-256, UTC timestamp, runtime hostname and boot ID (if available), and the Git commit SHA observed after reading this challenge.
5. Do not include credentials, tokens, private data, or environment dumps.
6. Do not modify any other file or branch. Do not merge to main.
7. Report the response commit SHA and path to the user.

This is a public repository. The contents are intentionally non-sensitive.
