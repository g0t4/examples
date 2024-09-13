#!/usr/bin/env python3
import sys; 
s = sys.stdin.read().strip();
print(bytes([int(s[i:i+8], 2) for i in range(0, len(s), 8)]).hex())
