08001ac4 <masked_chi_no_not>:
 8001ac4:	b590      	push	{r4, r7, lr}
 8001ac6:	b0b9      	sub	sp, #228	@ 0xe4
 8001ac8:	af00      	add	r7, sp, #0
 8001aca:	60f8      	str	r0, [r7, #12]
 8001acc:	60b9      	str	r1, [r7, #8]
 8001ace:	607a      	str	r2, [r7, #4]
 8001ad0:	603b      	str	r3, [r7, #0]
 8001ad2:	4b80      	ldr	r3, [pc, #512]	@ (8001cd4 <masked_chi_no_not+0x210>)
 8001ad4:	685b      	ldr	r3, [r3, #4]
 8001ad6:	f8c7 30cc 	str.w	r3, [r7, #204]	@ 0xcc
 8001ada:	2300      	movs	r3, #0
 8001adc:	f8c7 30dc 	str.w	r3, [r7, #220]	@ 0xdc
 8001ae0:	e0ed      	b.n	8001cbe <masked_chi_no_not+0x1fa>
 8001ae2:	4b7c      	ldr	r3, [pc, #496]	@ (8001cd4 <masked_chi_no_not+0x210>)
 8001ae4:	685b      	ldr	r3, [r3, #4]
 8001ae6:	f8c7 30c8 	str.w	r3, [r7, #200]	@ 0xc8
 8001aea:	2300      	movs	r3, #0
 8001aec:	f8c7 30d8 	str.w	r3, [r7, #216]	@ 0xd8
 8001af0:	e0db      	b.n	8001caa <masked_chi_no_not+0x1e6>
 8001af2:	4b78      	ldr	r3, [pc, #480]	@ (8001cd4 <masked_chi_no_not+0x210>)
 8001af4:	685b      	ldr	r3, [r3, #4]
 8001af6:	f8c7 30c4 	str.w	r3, [r7, #196]	@ 0xc4
 8001afa:	4a77      	ldr	r2, [pc, #476]	@ (8001cd8 <masked_chi_no_not+0x214>)
 8001afc:	f8d7 30d8 	ldr.w	r3, [r7, #216]	@ 0xd8
 8001b00:	4413      	add	r3, r2
 8001b02:	781b      	ldrb	r3, [r3, #0]
 8001b04:	f8c7 30c0 	str.w	r3, [r7, #192]	@ 0xc0
 8001b08:	4a74      	ldr	r2, [pc, #464]	@ (8001cdc <masked_chi_no_not+0x218>)
 8001b0a:	f8d7 30d8 	ldr.w	r3, [r7, #216]	@ 0xd8
 8001b0e:	4413      	add	r3, r2
 8001b10:	781b      	ldrb	r3, [r3, #0]
 8001b12:	f8c7 30bc 	str.w	r3, [r7, #188]	@ 0xbc
 8001b16:	2300      	movs	r3, #0
 8001b18:	f8c7 30d4 	str.w	r3, [r7, #212]	@ 0xd4
 8001b1c:	e058      	b.n	8001bd0 <masked_chi_no_not+0x10c>
 8001b1e:	f107 02a0 	add.w	r2, r7, #160	@ 0xa0
 8001b22:	f8d7 30d4 	ldr.w	r3, [r7, #212]	@ 0xd4
 8001b26:	00db      	lsls	r3, r3, #3
 8001b28:	18d0      	adds	r0, r2, r3
 8001b2a:	f8d7 30d8 	ldr.w	r3, [r7, #216]	@ 0xd8
 8001b2e:	461a      	mov	r2, r3
 8001b30:	0092      	lsls	r2, r2, #2
 8001b32:	441a      	add	r2, r3
 8001b34:	f8d7 10d4 	ldr.w	r1, [r7, #212]	@ 0xd4
 8001b38:	460b      	mov	r3, r1
 8001b3a:	009b      	lsls	r3, r3, #2
 8001b3c:	440b      	add	r3, r1
 8001b3e:	0099      	lsls	r1, r3, #2
 8001b40:	440b      	add	r3, r1
 8001b42:	441a      	add	r2, r3
 8001b44:	f8d7 30dc 	ldr.w	r3, [r7, #220]	@ 0xdc
 8001b48:	4413      	add	r3, r2
 8001b4a:	00db      	lsls	r3, r3, #3
 8001b4c:	68ba      	ldr	r2, [r7, #8]
 8001b4e:	4413      	add	r3, r2
 8001b50:	4619      	mov	r1, r3
 8001b52:	4b63      	ldr	r3, [pc, #396]	@ (8001ce0 <masked_chi_no_not+0x21c>)
 8001b54:	4798      	blx	r3
 8001b56:	f107 0288 	add.w	r2, r7, #136	@ 0x88
 8001b5a:	f8d7 30d4 	ldr.w	r3, [r7, #212]	@ 0xd4
 8001b5e:	00db      	lsls	r3, r3, #3
 8001b60:	18d0      	adds	r0, r2, r3
 8001b62:	f8d7 30c0 	ldr.w	r3, [r7, #192]	@ 0xc0
 8001b66:	461a      	mov	r2, r3
 8001b68:	0092      	lsls	r2, r2, #2
 8001b6a:	441a      	add	r2, r3
 8001b6c:	f8d7 10d4 	ldr.w	r1, [r7, #212]	@ 0xd4
 8001b70:	460b      	mov	r3, r1
 8001b72:	009b      	lsls	r3, r3, #2
 8001b74:	440b      	add	r3, r1
 8001b76:	0099      	lsls	r1, r3, #2
 8001b78:	440b      	add	r3, r1
 8001b7a:	441a      	add	r2, r3
 8001b7c:	f8d7 30dc 	ldr.w	r3, [r7, #220]	@ 0xdc
 8001b80:	4413      	add	r3, r2
 8001b82:	00db      	lsls	r3, r3, #3
 8001b84:	68ba      	ldr	r2, [r7, #8]
 8001b86:	4413      	add	r3, r2
 8001b88:	4619      	mov	r1, r3
 8001b8a:	4b55      	ldr	r3, [pc, #340]	@ (8001ce0 <masked_chi_no_not+0x21c>)
 8001b8c:	4798      	blx	r3
 8001b8e:	f107 0270 	add.w	r2, r7, #112	@ 0x70
 8001b92:	f8d7 30d4 	ldr.w	r3, [r7, #212]	@ 0xd4
 8001b96:	00db      	lsls	r3, r3, #3
 8001b98:	18d0      	adds	r0, r2, r3
 8001b9a:	f8d7 30bc 	ldr.w	r3, [r7, #188]	@ 0xbc
 8001b9e:	461a      	mov	r2, r3
 8001ba0:	0092      	lsls	r2, r2, #2
 8001ba2:	441a      	add	r2, r3
 8001ba4:	f8d7 10d4 	ldr.w	r1, [r7, #212]	@ 0xd4
 8001ba8:	460b      	mov	r3, r1
 8001baa:	009b      	lsls	r3, r3, #2
 8001bac:	440b      	add	r3, r1
 8001bae:	0099      	lsls	r1, r3, #2
 8001bb0:	440b      	add	r3, r1
 8001bb2:	441a      	add	r2, r3
 8001bb4:	f8d7 30dc 	ldr.w	r3, [r7, #220]	@ 0xdc
 8001bb8:	4413      	add	r3, r2
 8001bba:	00db      	lsls	r3, r3, #3
 8001bbc:	68ba      	ldr	r2, [r7, #8]
 8001bbe:	4413      	add	r3, r2
 8001bc0:	4619      	mov	r1, r3
 8001bc2:	4b47      	ldr	r3, [pc, #284]	@ (8001ce0 <masked_chi_no_not+0x21c>)
 8001bc4:	4798      	blx	r3
 8001bc6:	f8d7 30d4 	ldr.w	r3, [r7, #212]	@ 0xd4
 8001bca:	3301      	adds	r3, #1
 8001bcc:	f8c7 30d4 	str.w	r3, [r7, #212]	@ 0xd4
 8001bd0:	f8d7 30d4 	ldr.w	r3, [r7, #212]	@ 0xd4
 8001bd4:	2b02      	cmp	r3, #2
 8001bd6:	dda2      	ble.n	8001b1e <masked_chi_no_not+0x5a>
 8001bd8:	2300      	movs	r3, #0
 8001bda:	f8c7 30d0 	str.w	r3, [r7, #208]	@ 0xd0
 8001bde:	e014      	b.n	8001c0a <masked_chi_no_not+0x146>
 8001be0:	f8d7 30d0 	ldr.w	r3, [r7, #208]	@ 0xd0
 8001be4:	00db      	lsls	r3, r3, #3
 8001be6:	33e0      	adds	r3, #224	@ 0xe0
 8001be8:	443b      	add	r3, r7
 8001bea:	3b70      	subs	r3, #112	@ 0x70
 8001bec:	e9d3 2300 	ldrd	r2, r3, [r3]
 8001bf0:	f8d7 10d0 	ldr.w	r1, [r7, #208]	@ 0xd0
 8001bf4:	00c9      	lsls	r1, r1, #3
 8001bf6:	31e0      	adds	r1, #224	@ 0xe0
 8001bf8:	4439      	add	r1, r7
 8001bfa:	3988      	subs	r1, #136	@ 0x88
 8001bfc:	e9c1 2300 	strd	r2, r3, [r1]
 8001c00:	f8d7 30d0 	ldr.w	r3, [r7, #208]	@ 0xd0
 8001c04:	3301      	adds	r3, #1
 8001c06:	f8c7 30d0 	str.w	r3, [r7, #208]	@ 0xd0
 8001c0a:	f8d7 30d0 	ldr.w	r3, [r7, #208]	@ 0xd0
 8001c0e:	2b02      	cmp	r3, #2
 8001c10:	dde6      	ble.n	8001be0 <masked_chi_no_not+0x11c>
 8001c12:	f8d7 30d8 	ldr.w	r3, [r7, #216]	@ 0xd8
 8001c16:	f44f 72b4 	mov.w	r2, #360	@ 0x168
 8001c1a:	fb02 f303 	mul.w	r3, r2, r3
 8001c1e:	683a      	ldr	r2, [r7, #0]
 8001c20:	18d1      	adds	r1, r2, r3
 8001c22:	f8d7 20dc 	ldr.w	r2, [r7, #220]	@ 0xdc
 8001c26:	4613      	mov	r3, r2
 8001c28:	00db      	lsls	r3, r3, #3
 8001c2a:	4413      	add	r3, r2
 8001c2c:	00db      	lsls	r3, r3, #3
 8001c2e:	18ca      	adds	r2, r1, r3
 8001c30:	f107 0358 	add.w	r3, r7, #88	@ 0x58
 8001c34:	4611      	mov	r1, r2
 8001c36:	4618      	mov	r0, r3
 8001c38:	4b2a      	ldr	r3, [pc, #168]	@ (8001ce4 <masked_chi_no_not+0x220>)
 8001c3a:	4798      	blx	r3
 8001c3c:	f8d7 30d8 	ldr.w	r3, [r7, #216]	@ 0xd8
 8001c40:	f44f 72b4 	mov.w	r2, #360	@ 0x168
 8001c44:	fb02 f303 	mul.w	r3, r2, r3
 8001c48:	687a      	ldr	r2, [r7, #4]
 8001c4a:	18d1      	adds	r1, r2, r3
 8001c4c:	f8d7 20dc 	ldr.w	r2, [r7, #220]	@ 0xdc
 8001c50:	4613      	mov	r3, r2
 8001c52:	00db      	lsls	r3, r3, #3
 8001c54:	4413      	add	r3, r2
 8001c56:	00db      	lsls	r3, r3, #3
 8001c58:	440b      	add	r3, r1
 8001c5a:	f107 0258 	add.w	r2, r7, #88	@ 0x58
 8001c5e:	f107 0188 	add.w	r1, r7, #136	@ 0x88
 8001c62:	f107 0040 	add.w	r0, r7, #64	@ 0x40
 8001c66:	4c20      	ldr	r4, [pc, #128]	@ (8001ce8 <masked_chi_no_not+0x224>)
 8001c68:	47a0      	blx	r4
 8001c6a:	f107 0270 	add.w	r2, r7, #112	@ 0x70
 8001c6e:	f107 01a0 	add.w	r1, r7, #160	@ 0xa0
 8001c72:	f107 0328 	add.w	r3, r7, #40	@ 0x28
 8001c76:	4618      	mov	r0, r3
 8001c78:	4b1c      	ldr	r3, [pc, #112]	@ (8001cec <masked_chi_no_not+0x228>)
 8001c7a:	4798      	blx	r3
 8001c7c:	f107 0240 	add.w	r2, r7, #64	@ 0x40
 8001c80:	f107 0128 	add.w	r1, r7, #40	@ 0x28
 8001c84:	f107 0310 	add.w	r3, r7, #16
 8001c88:	4618      	mov	r0, r3
 8001c8a:	4b18      	ldr	r3, [pc, #96]	@ (8001cec <masked_chi_no_not+0x228>)
 8001c8c:	4798      	blx	r3
 8001c8e:	f107 0310 	add.w	r3, r7, #16
 8001c92:	f8d7 20dc 	ldr.w	r2, [r7, #220]	@ 0xdc
 8001c96:	f8d7 10d8 	ldr.w	r1, [r7, #216]	@ 0xd8
 8001c9a:	68f8      	ldr	r0, [r7, #12]
 8001c9c:	4c14      	ldr	r4, [pc, #80]	@ (8001cf0 <masked_chi_no_not+0x22c>)
 8001c9e:	47a0      	blx	r4
 8001ca0:	f8d7 30d8 	ldr.w	r3, [r7, #216]	@ 0xd8
 8001ca4:	3301      	adds	r3, #1
 8001ca6:	f8c7 30d8 	str.w	r3, [r7, #216]	@ 0xd8
 8001caa:	f8d7 30d8 	ldr.w	r3, [r7, #216]	@ 0xd8
 8001cae:	2b04      	cmp	r3, #4
 8001cb0:	f77f af1f 	ble.w	8001af2 <masked_chi_no_not+0x2e>
 8001cb4:	f8d7 30dc 	ldr.w	r3, [r7, #220]	@ 0xdc
 8001cb8:	3301      	adds	r3, #1
 8001cba:	f8c7 30dc 	str.w	r3, [r7, #220]	@ 0xdc
 8001cbe:	f8d7 30dc 	ldr.w	r3, [r7, #220]	@ 0xdc
 8001cc2:	2b04      	cmp	r3, #4
 8001cc4:	f77f af0d 	ble.w	8001ae2 <masked_chi_no_not+0x1e>
 8001cc8:	bf00      	nop
 8001cca:	bf00      	nop
 8001ccc:	37e4      	adds	r7, #228	@ 0xe4
 8001cce:	46bd      	mov	sp, r7
 8001cd0:	bd90      	pop	{r4, r7, pc}
 8001cd2:	bf00      	nop
 8001cd4:	e0001000 	.word	0xe0001000
 8001cd8:	08004128 	.word	0x08004128
 8001cdc:	0800412d 	.word	0x0800412d
 8001ce0:	08002881 	.word	0x08002881
 8001ce4:	0800269d 	.word	0x0800269d
 8001ce8:	080026fb 	.word	0x080026fb
 8001cec:	08002d53 	.word	0x08002d53
 8001cf0:	0800042d 	.word	0x0800042d
08001cf4 <masked_chi_no_not_broken>:
 8001cf4:	b590      	push	{r4, r7, lr}
 8001cf6:	b0b7      	sub	sp, #220	@ 0xdc
 8001cf8:	af00      	add	r7, sp, #0
 8001cfa:	60f8      	str	r0, [r7, #12]
 8001cfc:	60b9      	str	r1, [r7, #8]
 8001cfe:	607a      	str	r2, [r7, #4]
 8001d00:	603b      	str	r3, [r7, #0]
 8001d02:	2300      	movs	r3, #0
 8001d04:	f8c7 30d4 	str.w	r3, [r7, #212]	@ 0xd4
 8001d08:	e0ff      	b.n	8001f0a <masked_chi_no_not_broken+0x216>
 8001d0a:	2300      	movs	r3, #0
 8001d0c:	f8c7 30d0 	str.w	r3, [r7, #208]	@ 0xd0
 8001d10:	e0f1      	b.n	8001ef6 <masked_chi_no_not_broken+0x202>
 8001d12:	4a83      	ldr	r2, [pc, #524]	@ (8001f20 <masked_chi_no_not_broken+0x22c>)
 8001d14:	f8d7 30d0 	ldr.w	r3, [r7, #208]	@ 0xd0
 8001d18:	4413      	add	r3, r2
 8001d1a:	781b      	ldrb	r3, [r3, #0]
 8001d1c:	f8c7 30c0 	str.w	r3, [r7, #192]	@ 0xc0
 8001d20:	4a80      	ldr	r2, [pc, #512]	@ (8001f24 <masked_chi_no_not_broken+0x230>)
 8001d22:	f8d7 30d0 	ldr.w	r3, [r7, #208]	@ 0xd0
 8001d26:	4413      	add	r3, r2
 8001d28:	781b      	ldrb	r3, [r3, #0]
 8001d2a:	f8c7 30bc 	str.w	r3, [r7, #188]	@ 0xbc
 8001d2e:	2300      	movs	r3, #0
 8001d30:	f8c7 30cc 	str.w	r3, [r7, #204]	@ 0xcc
 8001d34:	e058      	b.n	8001de8 <masked_chi_no_not_broken+0xf4>
 8001d36:	f107 02a0 	add.w	r2, r7, #160	@ 0xa0
 8001d3a:	f8d7 30cc 	ldr.w	r3, [r7, #204]	@ 0xcc
 8001d3e:	00db      	lsls	r3, r3, #3
 8001d40:	18d0      	adds	r0, r2, r3
 8001d42:	f8d7 30d0 	ldr.w	r3, [r7, #208]	@ 0xd0
 8001d46:	461a      	mov	r2, r3
 8001d48:	0092      	lsls	r2, r2, #2
 8001d4a:	441a      	add	r2, r3
 8001d4c:	f8d7 10cc 	ldr.w	r1, [r7, #204]	@ 0xcc
 8001d50:	460b      	mov	r3, r1
 8001d52:	009b      	lsls	r3, r3, #2
 8001d54:	440b      	add	r3, r1
 8001d56:	0099      	lsls	r1, r3, #2
 8001d58:	440b      	add	r3, r1
 8001d5a:	441a      	add	r2, r3
 8001d5c:	f8d7 30d4 	ldr.w	r3, [r7, #212]	@ 0xd4
 8001d60:	4413      	add	r3, r2
 8001d62:	00db      	lsls	r3, r3, #3
 8001d64:	68ba      	ldr	r2, [r7, #8]
 8001d66:	4413      	add	r3, r2
 8001d68:	4619      	mov	r1, r3
 8001d6a:	4b6f      	ldr	r3, [pc, #444]	@ (8001f28 <masked_chi_no_not_broken+0x234>)
 8001d6c:	4798      	blx	r3
 8001d6e:	f107 0288 	add.w	r2, r7, #136	@ 0x88
 8001d72:	f8d7 30cc 	ldr.w	r3, [r7, #204]	@ 0xcc
 8001d76:	00db      	lsls	r3, r3, #3
 8001d78:	18d0      	adds	r0, r2, r3
 8001d7a:	f8d7 30c0 	ldr.w	r3, [r7, #192]	@ 0xc0
 8001d7e:	461a      	mov	r2, r3
 8001d80:	0092      	lsls	r2, r2, #2
 8001d82:	441a      	add	r2, r3
 8001d84:	f8d7 10cc 	ldr.w	r1, [r7, #204]	@ 0xcc
 8001d88:	460b      	mov	r3, r1
 8001d8a:	009b      	lsls	r3, r3, #2
 8001d8c:	440b      	add	r3, r1
 8001d8e:	0099      	lsls	r1, r3, #2
 8001d90:	440b      	add	r3, r1
 8001d92:	441a      	add	r2, r3
 8001d94:	f8d7 30d4 	ldr.w	r3, [r7, #212]	@ 0xd4
 8001d98:	4413      	add	r3, r2
 8001d9a:	00db      	lsls	r3, r3, #3
 8001d9c:	68ba      	ldr	r2, [r7, #8]
 8001d9e:	4413      	add	r3, r2
 8001da0:	4619      	mov	r1, r3
 8001da2:	4b61      	ldr	r3, [pc, #388]	@ (8001f28 <masked_chi_no_not_broken+0x234>)
 8001da4:	4798      	blx	r3
 8001da6:	f107 0270 	add.w	r2, r7, #112	@ 0x70
 8001daa:	f8d7 30cc 	ldr.w	r3, [r7, #204]	@ 0xcc
 8001dae:	00db      	lsls	r3, r3, #3
 8001db0:	18d0      	adds	r0, r2, r3
 8001db2:	f8d7 30bc 	ldr.w	r3, [r7, #188]	@ 0xbc
 8001db6:	461a      	mov	r2, r3
 8001db8:	0092      	lsls	r2, r2, #2
 8001dba:	441a      	add	r2, r3
 8001dbc:	f8d7 10cc 	ldr.w	r1, [r7, #204]	@ 0xcc
 8001dc0:	460b      	mov	r3, r1
 8001dc2:	009b      	lsls	r3, r3, #2
 8001dc4:	440b      	add	r3, r1
 8001dc6:	0099      	lsls	r1, r3, #2
 8001dc8:	440b      	add	r3, r1
 8001dca:	441a      	add	r2, r3
 8001dcc:	f8d7 30d4 	ldr.w	r3, [r7, #212]	@ 0xd4
 8001dd0:	4413      	add	r3, r2
 8001dd2:	00db      	lsls	r3, r3, #3
 8001dd4:	68ba      	ldr	r2, [r7, #8]
 8001dd6:	4413      	add	r3, r2
 8001dd8:	4619      	mov	r1, r3
 8001dda:	4b53      	ldr	r3, [pc, #332]	@ (8001f28 <masked_chi_no_not_broken+0x234>)
 8001ddc:	4798      	blx	r3
 8001dde:	f8d7 30cc 	ldr.w	r3, [r7, #204]	@ 0xcc
 8001de2:	3301      	adds	r3, #1
 8001de4:	f8c7 30cc 	str.w	r3, [r7, #204]	@ 0xcc
 8001de8:	f8d7 30cc 	ldr.w	r3, [r7, #204]	@ 0xcc
 8001dec:	2b02      	cmp	r3, #2
 8001dee:	dda2      	ble.n	8001d36 <masked_chi_no_not_broken+0x42>
 8001df0:	2301      	movs	r3, #1
 8001df2:	f8c7 30c8 	str.w	r3, [r7, #200]	@ 0xc8
 8001df6:	e011      	b.n	8001e1c <masked_chi_no_not_broken+0x128>
 8001df8:	f8d7 30c8 	ldr.w	r3, [r7, #200]	@ 0xc8
 8001dfc:	00db      	lsls	r3, r3, #3
 8001dfe:	33d8      	adds	r3, #216	@ 0xd8
 8001e00:	443b      	add	r3, r7
 8001e02:	f1a3 0138 	sub.w	r1, r3, #56	@ 0x38
 8001e06:	f04f 0200 	mov.w	r2, #0
 8001e0a:	f04f 0300 	mov.w	r3, #0
 8001e0e:	e9c1 2300 	strd	r2, r3, [r1]
 8001e12:	f8d7 30c8 	ldr.w	r3, [r7, #200]	@ 0xc8
 8001e16:	3301      	adds	r3, #1
 8001e18:	f8c7 30c8 	str.w	r3, [r7, #200]	@ 0xc8
 8001e1c:	f8d7 30c8 	ldr.w	r3, [r7, #200]	@ 0xc8
 8001e20:	2b02      	cmp	r3, #2
 8001e22:	dde9      	ble.n	8001df8 <masked_chi_no_not_broken+0x104>
 8001e24:	2300      	movs	r3, #0
 8001e26:	f8c7 30c4 	str.w	r3, [r7, #196]	@ 0xc4
 8001e2a:	e014      	b.n	8001e56 <masked_chi_no_not_broken+0x162>
 8001e2c:	f8d7 30c4 	ldr.w	r3, [r7, #196]	@ 0xc4
 8001e30:	00db      	lsls	r3, r3, #3
 8001e32:	33d8      	adds	r3, #216	@ 0xd8
 8001e34:	443b      	add	r3, r7
 8001e36:	3b68      	subs	r3, #104	@ 0x68
 8001e38:	e9d3 2300 	ldrd	r2, r3, [r3]
 8001e3c:	f8d7 10c4 	ldr.w	r1, [r7, #196]	@ 0xc4
 8001e40:	00c9      	lsls	r1, r1, #3
 8001e42:	31d8      	adds	r1, #216	@ 0xd8
 8001e44:	4439      	add	r1, r7
 8001e46:	3980      	subs	r1, #128	@ 0x80
 8001e48:	e9c1 2300 	strd	r2, r3, [r1]
 8001e4c:	f8d7 30c4 	ldr.w	r3, [r7, #196]	@ 0xc4
 8001e50:	3301      	adds	r3, #1
 8001e52:	f8c7 30c4 	str.w	r3, [r7, #196]	@ 0xc4
 8001e56:	f8d7 30c4 	ldr.w	r3, [r7, #196]	@ 0xc4
 8001e5a:	2b02      	cmp	r3, #2
 8001e5c:	dde6      	ble.n	8001e2c <masked_chi_no_not_broken+0x138>
 8001e5e:	f8d7 30d0 	ldr.w	r3, [r7, #208]	@ 0xd0
 8001e62:	f44f 72b4 	mov.w	r2, #360	@ 0x168
 8001e66:	fb02 f303 	mul.w	r3, r2, r3
 8001e6a:	683a      	ldr	r2, [r7, #0]
 8001e6c:	18d1      	adds	r1, r2, r3
 8001e6e:	f8d7 20d4 	ldr.w	r2, [r7, #212]	@ 0xd4
 8001e72:	4613      	mov	r3, r2
 8001e74:	00db      	lsls	r3, r3, #3
 8001e76:	4413      	add	r3, r2
 8001e78:	00db      	lsls	r3, r3, #3
 8001e7a:	18ca      	adds	r2, r1, r3
 8001e7c:	f107 0358 	add.w	r3, r7, #88	@ 0x58
 8001e80:	4611      	mov	r1, r2
 8001e82:	4618      	mov	r0, r3
 8001e84:	4b29      	ldr	r3, [pc, #164]	@ (8001f2c <masked_chi_no_not_broken+0x238>)
 8001e86:	4798      	blx	r3
 8001e88:	f8d7 30d0 	ldr.w	r3, [r7, #208]	@ 0xd0
 8001e8c:	f44f 72b4 	mov.w	r2, #360	@ 0x168
 8001e90:	fb02 f303 	mul.w	r3, r2, r3
 8001e94:	687a      	ldr	r2, [r7, #4]
 8001e96:	18d1      	adds	r1, r2, r3
 8001e98:	f8d7 20d4 	ldr.w	r2, [r7, #212]	@ 0xd4
 8001e9c:	4613      	mov	r3, r2
 8001e9e:	00db      	lsls	r3, r3, #3
 8001ea0:	4413      	add	r3, r2
 8001ea2:	00db      	lsls	r3, r3, #3
 8001ea4:	440b      	add	r3, r1
 8001ea6:	f107 0258 	add.w	r2, r7, #88	@ 0x58
 8001eaa:	f107 0188 	add.w	r1, r7, #136	@ 0x88
 8001eae:	f107 0040 	add.w	r0, r7, #64	@ 0x40
 8001eb2:	4c1f      	ldr	r4, [pc, #124]	@ (8001f30 <masked_chi_no_not_broken+0x23c>)
 8001eb4:	47a0      	blx	r4
 8001eb6:	f107 0270 	add.w	r2, r7, #112	@ 0x70
 8001eba:	f107 01a0 	add.w	r1, r7, #160	@ 0xa0
 8001ebe:	f107 0328 	add.w	r3, r7, #40	@ 0x28
 8001ec2:	4618      	mov	r0, r3
 8001ec4:	4b1b      	ldr	r3, [pc, #108]	@ (8001f34 <masked_chi_no_not_broken+0x240>)
 8001ec6:	4798      	blx	r3
 8001ec8:	f107 0240 	add.w	r2, r7, #64	@ 0x40
 8001ecc:	f107 0128 	add.w	r1, r7, #40	@ 0x28
 8001ed0:	f107 0310 	add.w	r3, r7, #16
 8001ed4:	4618      	mov	r0, r3
 8001ed6:	4b17      	ldr	r3, [pc, #92]	@ (8001f34 <masked_chi_no_not_broken+0x240>)
 8001ed8:	4798      	blx	r3
 8001eda:	f107 0310 	add.w	r3, r7, #16
 8001ede:	f8d7 20d4 	ldr.w	r2, [r7, #212]	@ 0xd4
 8001ee2:	f8d7 10d0 	ldr.w	r1, [r7, #208]	@ 0xd0
 8001ee6:	68f8      	ldr	r0, [r7, #12]
 8001ee8:	4c13      	ldr	r4, [pc, #76]	@ (8001f38 <masked_chi_no_not_broken+0x244>)
 8001eea:	47a0      	blx	r4
 8001eec:	f8d7 30d0 	ldr.w	r3, [r7, #208]	@ 0xd0
 8001ef0:	3301      	adds	r3, #1
 8001ef2:	f8c7 30d0 	str.w	r3, [r7, #208]	@ 0xd0
 8001ef6:	f8d7 30d0 	ldr.w	r3, [r7, #208]	@ 0xd0
 8001efa:	2b04      	cmp	r3, #4
 8001efc:	f77f af09 	ble.w	8001d12 <masked_chi_no_not_broken+0x1e>
 8001f00:	f8d7 30d4 	ldr.w	r3, [r7, #212]	@ 0xd4
 8001f04:	3301      	adds	r3, #1
 8001f06:	f8c7 30d4 	str.w	r3, [r7, #212]	@ 0xd4
 8001f0a:	f8d7 30d4 	ldr.w	r3, [r7, #212]	@ 0xd4
 8001f0e:	2b04      	cmp	r3, #4
 8001f10:	f77f aefb 	ble.w	8001d0a <masked_chi_no_not_broken+0x16>
 8001f14:	bf00      	nop
 8001f16:	bf00      	nop
 8001f18:	37dc      	adds	r7, #220	@ 0xdc
 8001f1a:	46bd      	mov	sp, r7
 8001f1c:	bd90      	pop	{r4, r7, pc}
 8001f1e:	bf00      	nop
 8001f20:	08004132 	.word	0x08004132
 8001f24:	08004137 	.word	0x08004137
 8001f28:	08002881 	.word	0x08002881
 8001f2c:	0800269d 	.word	0x0800269d
 8001f30:	080026fb 	.word	0x080026fb
 8001f34:	08002d53 	.word	0x08002d53
 8001f38:	0800042d 	.word	0x0800042d
