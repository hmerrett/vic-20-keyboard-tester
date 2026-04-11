# HenryTests VIC-20 Keyboard Tester - Build Guide

VIC-20 keyboard matrix tester ROM cartridge. Scans the 8x8 keyboard matrix via VIA #2 hardware and displays column/row state in real time on screen. Completely standalone with no KERNAL dependency.

## Files

| File | Description |
|---|---|
| `assemble.py` | Python 3 source / assembler. Edit this to change the program, then run it to rebuild. |
| `kbtest.bin` | Raw 8K ROM image (8192 bytes, maps to $A000-$BFFF). Burn this to an EPROM. |
| `kbtest.prg` | Same ROM with a 2-byte $A000 load address header prepended (8194 bytes). For VICE. |
| `kbtest.hex` | Intel HEX format of the ROM image. For EPROM programmers that prefer HEX input. |

## Building from Source

The only dependency is Python 3 (any version from 3.6 onwards). No external assembler, no pip packages.

```
python3 assemble.py
```

This produces `kbtest.bin`, `kbtest.prg`, and `kbtest.hex` in the current directory.

Note: the VIC chip registers are set for PAL timing. On an NTSC VICE setup the display may be offset but should still be visible.

## Burning to EPROM

You need a 2764 EPROM (8Kx8, 28-pin DIP) and a programmer such as a TL866II Plus, MiniPro, or similar.

1. Program and verify `kbtest.bin` to the EPROM.
2. Fit the EPROM into a VIC-20 cartridge PCB wired for the $A000 block (active on BLK5, the standard 8K auto-start slot).


## How It Works

The program is entirely standalone and does not call any KERNAL routines. On entry it:

1. Sets up the CPU (SEI, CLD, sets the stack pointer).
2. Initialises the VIC chip ($9000-$900F) for a standard PAL 22x23 text display.
3. Clears screen memory ($1E00) and colour RAM ($9600) directly.
4. Writes static labels to screen memory using raw screen codes.
5. Configures VIA #2 Port B ($9120) as output for keyboard column drive and Port A ($9121) as input for row read.
6. Enters an infinite loop: for each of the 8 columns, it drives that column low, reads the rows, and writes the result (as dots, asterisks, and hex) directly to the corresponding screen memory location.

The keyboard matrix mapping follows the standard VIC-20 layout (write to $9120 column, read from $9121 row). A `*` in the display means that matrix intersection is closed (key pressed). The `SCAN:` line shows the scan code of the first detected key, computed as `column * 8 + row_bit_position`.

## Modifying

Everything is in `assemble.py`. The `Asm6502` class at the top is a minimal 6502 assembler. The program itself follows below it as a sequence of method calls. To change text, edit the `title_text`, `subtitle`, or `subtitle2` strings. To change colours, edit the `$900F` value (background/border) and the colour RAM fill value. Rebuild with `python3 assemble.py`.
