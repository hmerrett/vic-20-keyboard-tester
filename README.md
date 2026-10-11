# HenryTests VIC-20 Keyboard Tester

VIC-20 keyboard matrix tester ROM cartridge, in Retro Hardware Discord (RHD) colours. Scans the 8x8 keyboard matrix via VIA #2 hardware and displays column/row state in real time on screen. Completely standalone with no KERNAL dependency.

The screen has a colour-cycling RHD logo and rainbow stripe, the live matrix grid, the name of the key being held, RESTORE and joystick status, and a progress bar counting up to all 65 keys.

## Files

| File | Description |
|---|---|
| `assemble.py` | Python 3 source / assembler. Edit this to change the program, then run it to rebuild. |
| `kbtest.bin` | Raw 8K ROM image (8192 bytes, maps to $A000-$BFFF). Burn this to an EPROM. |
| `kbtest.prg` | Same ROM with a 2-byte $A000 load address header prepended (8194 bytes). For VICE. |
| `kbtest.hex` | Intel HEX format of the ROM image. For EPROM programmers that prefer HEX input. |

## Building from Source

The only dependency is Python 3 (any version from 3.6 onwards). 

```
python3 assemble.py
```

This produces `kbtest.bin`, `kbtest.prg`, and `kbtest.hex` in the current directory.

Note: the VIC chip registers are set for PAL timing. 

## Burning to EPROM

You need a 2764 EPROM (8Kx8, 28-pin DIP) and a programmer such as a TL866II Plus, MiniPro, or similar.

1. Program and verify `kbtest.bin` to the EPROM.
2. Fit the EPROM into a VIC-20 cartridge PCB wired for the $A000 block (active on BLK5, the standard 8K auto-start slot).


## How It Works

The program is entirely standalone and does not call any KERNAL routines. The main loop is locked to the frame rate: it waits for the raster to reach the top of the screen, then scans and redraws, so updates never tear.

Each grid row is one keyboard column (`C0`-`C7`, driven on VIA2 PB). Its eight cells are the row bits read back on VIA2 PA, bit 7 on the left to bit 0 on the right (numbered in the header), followed by the raw row byte in hex. Each cell shows one of three states:

| Symbol | Meaning |
|---|---|
| yellow `█` | Key is pressed **right now** (live). This always shows, so retesting an already-tested key still flags up. |
| (blank) | Key has been pressed at least once and is now released — i.e. it has been "ticked off". |
| red `●` | Key has **never** been pressed since power-on. |

This makes coverage testing easy: work through the keyboard and watch the red dots disappear. Each `Cn` label turns green once all eight keys in its column have registered. When you have pressed every key, any remaining `●` marks the intersections that never registered — those are the keys (or matrix lines) to investigate.

The persistent state is held in an 8-byte "seen" bitmap in the tape buffer at `$0340`. To reset it, just reset/power-cycle the machine.

The `SCAN` line shows the scan code of the first detected key, computed as `column * 8 + row_bit_position`, and that key's name (from the same layout as the KERNAL's keyboard table). If the name doesn't match the key you pressed, look for a wiring fault.

### Progress and sound

The bar and `nn/65` counter at the bottom track how many of the 65 keys (the 64 matrix keys plus RESTORE) have registered. When the count reaches 65, the border turns green, `ALL KEYS TESTED!` appears and a short jingle plays. The SHIFT LOCK key shares its matrix position with left SHIFT, so it can't be told apart.

Each key or joystick input gives a short blip on its first press, so you can work through the keyboard without watching the screen.

### RESTORE

The **RESTORE** key is not part of the 8x8 matrix — it is wired to the CA1 input of VIA #1, which is the machine's NMI source. It therefore has its own `RESTORE` cell, using the same coverage convention as the grid; the label turns green once it has registered.

Rather than taking an actual NMI, the program disables VIA #1 interrupts and polls the CA1 edge flag (`$911D` bit 1) once per scan. Because the flag is edge-latched, even a brief tap is caught, and clearing it after each read re-arms detection so repeated presses keep registering.

### Joystick

The control port is read once per scan and shown as a d-pad of five lettered cells — `U` `D` `L` `R` around `F` (fire) — each using the same coverage convention. Each letter turns green once that input has registered, and `JOYSTICK` turns green when all five have. The switches are active-low and split across both VIAs:

| Direction | Register | Bit |
|---|---|---|
| Up | VIA1 PA `$911F` | 2 |
| Down | VIA1 PA `$911F` | 3 |
| Left | VIA1 PA `$911F` | 4 |
| Fire | VIA1 PA `$911F` | 5 |
| Right | VIA2 PB `$9120` | 7 |

Port A is read through `$911F`, the no-handshake mirror of `$9111`, because reading `$9111` would clear a pending RESTORE edge. Right shares its line with keyboard column 7, so to read it the program drives PB high, briefly switches `VIA2 DDRB` bit 7 to input, samples `$9120`, then restores the column as an output. Driving the line high first means it isn't still low from the column scan when it's sampled. In VICE, enable a joystick on the control port and map it to test (Settings → Joystick).

## Modifying

Everything is in `assemble.py`. The `Asm6502` class at the top is a minimal 6502 assembler. The static screen (logo, labels, colours) is laid out next with `put()` calls into a screen image and colour image, which the ROM copies into place at start-up. The program itself follows as a sequence of method calls. Rebuild with `python3 assemble.py`.
