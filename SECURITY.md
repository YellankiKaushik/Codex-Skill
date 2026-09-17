# Security Policy

Do not paste credentials, private keys, tokens, or other secrets into public issues, discussions, screenshots, or logs.

This plugin intentionally blocks common secret-bearing paths such as `.env`, `.env.*`, `credentials.json`, `service-account.json`, `*.pem`, `*.key`, `id_rsa`, `id_ed25519`, `secrets.*`, `private-key.*`, and `firebase-adminsdk*.json` before staging or pushing unexpected files.

Filename detection is a heuristic and cannot guarantee that every secret is caught. Use GitHub secret scanning, branch protections, and repository access controls where available.

If the skill stages or commits something that appears secret-bearing unexpectedly, stop using the affected branch, rotate the credential, and report the behavior with a reproduction that does not include the secret value.
