# Dell PFS BIOS Assembler
This script makes **Downgrade-able BIOS update** file from Dell original BIOS updates.  

Tutorial: [Downgrade BIOS on Dell's blocked downgrade machines][0]

Discuss on reddit: [I can Downgrade Dell BIOS to older version by making new Dell BIOS update file][6]

**READ BELOW CAREFULLY**

*Even thought inputs of assembler are Dell's original and signed files, downgrading to older BIOS version without understanding about how BIOS components work together can harm your machine.*

*BIOS can be downgraded easily, but Intel ME may not because Intel ME has its own update engine. Main BIOS updater just sends Intel ME FW to ME Engine. You mostly will see a message that "Send Intel ME FW to ..." and it may fail*

*Some BIOS was changed totally in memory map from an old version to a newer version. Please read Dell BIOS update warning carefully. If Dell claims that "once you update BIOS to Y version, you can not go back to X version due to abc, please DO NOT go back further than X. For example, Dell Vostro 7580, from BIOS 1.6.1, it changed system map to include BIOS Remote, so If you're at a higher version, please DO NOT go back to 1.6.1 or ealier one. I broke one of my laptop because of that T.T*
  
***Do it with your own risk.***

## Old BIOS version has better performance and power usage
I have a **Dell Vostro 7580** and use **ThrottleStop** to undervolt, monitor power state, and benchmark
Below tests were measured with the same conditions of drivers, hardware, except BIOS update. I wrote it in [this comment][5]

**on BIOS 1.11.1**  
- Benchmark for 1024MB on 12 threads took around 120 seconds
- In idle, when plug both external HDMI and VGA, CPU was 90% of time at C7 power package state, and consumed only 0.5W

**on BIOS 1.12.2**  
- Benchmark for the same 1024MB on 12 thread took 145 seconds or more 
- In idle, when plug both external HDMI and VGA, CPU was 40% of time at C7 power package state, and consumed upto 12W. This is a huge number compared to 0.5W !!!

There obviously are performance and power issues after upgrading to new BIOS.

**Therefore, I really want to downgrade**

## Problems of Blocked Downgrade
Recently, Dell has locked BIOS Downgrade functions on some laptop products because they don't allow users to go back to an older BIOS version which had security problems.
Force downgrading using older Dell BIOS files will show a red message "**BIOS Update blocked due to unsupported downgrade**".  

There are some methods to unlock Flash chipset then re-flash older BIOS in the thread [[Guide] Unlock Intel Flash Descriptor Read/Write Access Permissions for SPI Servicing][1] but they are difficult to do.

I tried to re-flash BIOS on my Dell Vostro 7580 with Flash Programming Tool in [Intel (CS)ME System Tools][2], so below are the options:
* **PinMod method/Hardware SPI programmer**: I couldn't do this because of warranty stamps on the back cover
* **Service jumper, Service tools**: I could not find them on the internet
* **Update option in BIOS**: it has option to downgrade but it doesn't work, there is no option to enable re-flash
* **Use *setup_var* to enable BIOS/ME descriptor**: I tried but after setting new values in efi boot, BIOS automatically resets them to default values

So, I've failed to downgrade BIOS.

## Make new BIOS update file 
I come up with an idea of replacing an old BIOS payload in a new BIOS update file, and **it works**

### 1. Extract entries from Dell Firmware Update Utilities
I have modified [Dell PFS BIOS Extractor][3] (based on [Plato Mavropoulos's script][4]) to extract Dell Firmware Update Utilities (FUU) exe file to raw BIOS entries. Each entry has its header and signed payloads.
There are some entries included in Dell FUU: 
* **Model Information**: information to check version of firmware, model
* **PFS Information**: list of GUIDs if included entries in FUU
* **BIOS**: payload to flash into BIOS region
* **EC**: Embedded Controller's firmware
* **ME**: Intel (CS)ME's firmware
* some other utilities in BIOS

I have to extract BIOS entries from 2 Dell FUU files:
1. FUU file at current version of running BIOS, i.e. 1.12.2
```sh
python Dell_PFS_Extract.py -d Vostro_7580_1.12.2.exe
```
2. FUU file at lower version which I want to downgrade to, i.e. 1.11.1 
```sh
python Dell_PFS_Extract.py -d Vostro_7580_1.11.1.exe
```
After extracting, I will re-assemble them into new Dell FUU file.

### 2. Re-assemble entries to make new Firmware Update file
To fool Dell system to think that new FUU is the same version with its running version, I must use **Model Information** and **PFS Information** entries from current FUU version (1.12.2).
Then I can use other entries from older FUU version (BIOS v1.11.1, EC v1.11.1, etc.,).

I wrote [**Dell PFS BIOS Assembler**][3] to merge entries into a new FUU. Those entries are:
* **__exe_begin.bin**: the begging part of Dell FUU exe file
* **__exe_end.bin**: the ending part of Dell FUU exe file
* **Modem Information-1.12.2**: to fake BIOS payload version
* **FPS Information-1.12.2**: to have list of included entry GUIDs
* **BIOS-1.11.1**: BIOS entry of older Dell FUU, we will downgrade BIOS to this version
* **EC-1.11.1**: Embedded Controller of older Dell FUU, we will downgrade BIOS to this version
* other entries can use 1.12.2 version or 1.11.1 version (ME may not be downgraded, it uses Intel ME Updater)

![files.png](files.PNG)

```sh
python Dell_PFS_Assembler.py -f downgrade_to_1.11.1
```
After running the assembler, you will get new Dell FUU file as *__output.exe*. Rename it if needed.

### 3. A note before downgrading
Because downgrading can cause mismatched data problem, some functions on windows may not work normally. I had finger scanner problem after downgrading.
Therefore, you should think about the side effect before re-flashing.

### 4. Re-flash
Execute the new FUU file, or use BIOS Flash Programmer in BIOS menu. After downgrading, re-check your BIOS version and fix issues if needed.

---
Tutorial: [Downgrade BIOS on Dell's blocked downgrade machines][0]

[0]: https://youtu.be/7zFAU9DKmVk
[1]: https://www.win-raid.com/t3553f39-Guide-Unlock-Intel-Flash-Descriptor-Read-Write-Access-Permissions-for-SPI-Servicing.html
[2]: https://www.win-raid.com/t596f39-Intel-Management-Engine-Drivers-Firmware-amp-System-Tools.html
[3]: https://github.com/vuquangtrong/Dell-PFS-BIOS-Assembler
[4]: https://github.com/platomav/BIOSUtilities
[5]: https://www.reddit.com/r/Dell/comments/f45fp4/dell_g5_5587g7_7588_and_vostro_7580_bios_1122/fwk2kbp/
[6]: https://www.reddit.com/r/Dell/comments/i2dttg/i_can_downgrade_dell_bios_to_older_version_by/
