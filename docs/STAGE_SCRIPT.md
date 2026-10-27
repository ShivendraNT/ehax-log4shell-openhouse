# Stage Script — Log4Shell Wallpaper Reveal

**Audience:** school kids, 4–6 per batch
**Setup:** victim laptop facing the kids with the **normal wallpaper** visible.
The Minecraft server terminal is minimised. Attacker laptop is with the
presenter/operator, terminal ready at the trigger prompt.
**Golden rule:** the demo is the wallpaper, not a shell. Keep it harmless.

---

## Version A — full station script (~4–5 min)

### 0:00 — Intro (25 sec)

> “Hi! Hum **EHAX** se hain — DTU ki cybersecurity society. Aaj hum dikhayenge
> ki ek chhota sa bug kaise poore computer ko control kar sakta hai — **bina
> password, bina kuch hack karne jaisa dikhne wale tareeke se**. Bas ek text
> message.”

*Cue: point to the victim laptop. Let them look at the normal wallpaper.*

### 0:25 — Setup (25 sec)

> “Ye ek **Minecraft server** hai. Jab bhi koi chat mein kuch type karta hai,
> server use apni **log file** mein save karta hai — bilkul normal cheez, jaise
> ek diary. Lekin is server ke andar ek purani library thi jiska naam **log4j**
> hai. Usme ek chhoti si galti thi.”

*Cue: don't explain the syntax yet. Keep it simple.*

### 0:50 — Hand-off (15 sec)

> “Chalo tum [kid's name] ye message chat mein bhejo.”
> *(If the kid is shy: “Bas Enter press karo — message already ready hai.”)*

*Cue: operator gives the attacker laptop / presses Enter. The kid can type the
pre-copied trigger or simply press Enter. The message must be the exact
pre-copied string; don't read it aloud or write it on a board.*

### 1:00 — Wait (3–5 sec)

**Silence.** Let the server think. Don't fill the pause.

### 1:05 — Reveal

> “Dekho screen pe!”

*Cue: victim wallpaper changes to the EHAX reveal image. Let the kids react.
Point at the screen; don't talk over the first reaction.*

### 1:20 — Explain what happened (35 sec)

> “Jaise hi tumne wo message bheja, server ne use apni log mein likha. Log4j ne
> us text ko ek **special instruction** samajh liya — aur apne aap doosre
> computer se connect karke ek code file download kar li, aur chala diya. Is
> baar humne bas **wallpaper change** karwaya — harmless. Lekin ek real
> attacker isi raste se tumhari files padh sakta tha, data chura sakta tha, ya
> malware chala sakta tha.”

**Accuracy note for presenters:** the code runs with the Minecraft server
process's permissions. If the server runs as a normal user, the attacker gets
that user's access; if it runs as admin/root, it's worse. Don't claim “root on
every machine” — say “jitna access server process ke paas hai.”

### 1:55 — Why it matters (20 sec)

> “Isiliye **software update** karte rehna zaroori hai. Ye bug 2021 mein mila
> tha aur patch ho chuka hai. Hum ise sirf ek **isolated, safe network** pe dikha
> rahe hain. Apne ya kisi aur ke system pe bina permission try karna **illegal**
> hai — IT Act ke under punishable. Sirf apne lab ya permission wale system pe.”

*Cue: say the legal line every single batch. No exceptions.*

### 2:15 — Close / Q&A

> “Koi sawaal? Nahi toh next group!”

*Cue: operator/reset runner restores the snapshot or runs `reset-wallpaper.sh`
while the next group queues.*

---

## Version B — 90-second crowd version

Use when the queue is long. Skip the Minecraft explanation detail; keep the
demo and the legal line.

> “Hum EHAX se hain, DTU ki cybersecurity society. Ye ek purana Minecraft server
> hai. Isme ek logging library thi jisme ek bug tha. Ek chat message bhejte hain —
> dekho kya hota hai.”
>
> *(Kid presses Enter. 3-second pause. Wallpaper changes.)*
>
> “Server ne wo message log kiya, library ne usse ek remote instruction samajh
> liya, aur code download karke chala diya. Is baar sirf wallpaper change hua.
> Real attacker files padh sakta tha. Isliye updates karo. Aur bina permission
> kisi ke system pe try mat karo — illegal hai. Sawaal?”

---

## FAQ card for presenters

**“Kya ye abhi bhi kaam karta hai?”**
> “Patched Minecraft/Java versions mein nahi. Purane unpatched systems mein
> risk abhi bhi ho sakta hai. Isliye updates aur patching important hai.”

**“Kya hum bhi kar sakte hain?”**
> “Seekh sakte ho — apne system pe, safe labs, CTFs, ya permission ke saath.
> Kisi aur ke laptop/phone pe bina permission karna illegal hai.”

**“Password kya tha?”**
> “Koi password nahi tha. Bug ne server ko bola: ‘is address se code laao aur
> chalao.’ Server ne apne aap kar diya.”

**“Kya aapne hamara data chura liya?”**
> “Nahi. Hum sirf apni isolated VM mein wallpaper change kar rahe hain. Real
> attacker ke paas files padhne ka access ho sakta tha — isliye ye bug serious
> tha.”

**“Kya ye mere phone pe bhi hoga?”**
> “Ye Java library ka bug hai, mainly Java apps/servers pe. Har phone affected
> nahi hota. Lekin software updates sab jagah important hain.”

**“Aap hackers ho?”**
> “Hum ethical hackers/security researchers hain. Hum permission ke saath,
> apne lab mein testing karte hain — kisi ko nuksaan pahunchane ke liye nahi.”

**“Hacker kaise bante hain?”**
> “Programming, networking, Linux, CTFs, safe labs. EHAX workshops/hackathons
> mein aa sakte ho. Legal aur ethical rehna sabse important hai.”

**“Ye illegal hai kya?”**
> “Yeh demo permission ke saath, isolated lab mein hai — isliye legal. Bina
> permission kisi aur ke system pe karna illegal hai.”

**“Kya aapne humara laptop hack kiya?”**
> “Nahi. Ye hamara alag victim VM hai; tumhara laptop is network pe nahi hai.”

---

## Presenter do / don't

**Do**

- Point at the victim screen, not the attacker terminal.
- Use the 3–5 second pause before the reveal.
- Say “isolated, safe network” and “bina permission illegal” every batch.
- Let the kids react; don't rush to the explanation.
- Keep the explanation at “message → log → library → remote code → wallpaper.”
- Use the backup video only if the live demo fails; don't pretend it's live.

**Don't**

- Don't read the full trigger syntax aloud or write it on a whiteboard.
- Don't call it “hacking a real laptop” or “full root” unless it's true.
- Don't show a reverse shell or real file access “for fun.”
- Don't let a kid try it on their own device.
- Don't skip the disclaimer because the group is small.
- Don't debug in silence; use the recovery line and keep the room.

---

## Recovery line (if the wallpaper doesn't change)

> “Ek second — server ko dobara bhejte hain. Dekho, log mein message aana
> chahiye… [operator retries]”

If it still fails:

> “Interesting — demo bhi patch ho gaya lagta hai! Chalo main dikhata hoon ki
> normally kya hota hai.”

*Cue: show the 20-second backup recording. Between batches, fix the live setup.
Never claim a pre-recorded clip is live.*

---

## Key lines to repeat every batch

1. “Ye bug **2021** mein mila tha aur **patch ho chuka hai**.”
2. “Hum **isolated, air-gapped VMs** pe hain — koi real system nahi.”
3. “**Bina permission** kisi aur ke system pe try karna **illegal** hai.”
4. “Is baar humne sirf **wallpaper** change karwaya — real attacker ke paas
   zyada access ho sakta tha.”
5. “**Update karte rehna** — yahi asli lesson hai.”
