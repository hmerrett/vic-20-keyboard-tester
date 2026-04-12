# HenryTests VIC-20 Keyboard Tester

VIC-20 keyboard matrix tester ROM cartridge. Scans the 8x8 keyboard matrix via VIA #2 hardware and displays column/row state in real time on screen. Completely standalone with no KERNAL dependency.

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

The program is entirely standalone and does not call any KERNAL routines.

A `*` in the display means that matrix intersection is closed (key pressed). The `SCAN:` line shows the scan code of the first detected key, computed as `column * 8 + row_bit_position`.

## Modifying

Everything is in `assemble.py`. The `Asm6502` class at the top is a minimal 6502 assembler. The program itself follows below it as a sequence of method calls. Rebuild with `python3 assemble.py`.
