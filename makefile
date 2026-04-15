# Hey Emacs, this is a -*- makefile -*-
#----------------------------------------------------------------------------
# Makefile for ChipWhisperer SimpleSerial-Keccak Program
#----------------------------------------------------------------------------

# Target file name (without extension)
TARGET = simpleserial-base

SS_VER = SS_VER_2_1

# List C source files here
SRC += simpleserial-base.c \

CFLAGS  += -Og -mlong-calls -g
LDFLAGS += -mlong-calls


# List additional headers if required
# (Not strictly necessary unless custom build rules)
# HDRS += masked_keccak.h masked_gadgets.h masked_types.h sha_shake.h params.h

# -----------------------------------------------------------------------------
# Add simpleserial project to build
include ../simpleserial/Makefile.simpleserial

FIRMWAREPATH = ../.
include $(FIRMWAREPATH)/Makefile.inc