# Dell PFS BIOS Assembler
This script makes **Downgrade-able BIOS update** file from Dell original BIOS updates.  
Tutorial: [Downgrade BIOS on Dell's blocked downgrade machines](https://youtube.com/)

## Problems of Blocked Downgrade
Recently, Dell has locked BIOS Downgrade functions on some laptop lines because they don't allow to go back to an older BIOS version which had security problems.
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
python Dell_PFS_Extract.py -x Vostro_7580_1.12.2.exe
```
2. FUU file at lower version which I want to downgrade to, i.e. 1.11.1 
```sh
python Dell_PFS_Extract.py -x Vostro_7580_1.11.1.exe
```
After extracting, I will re-assemble them into new Dell FUU file.

### 2. Re-assemble entries to make new Firmware Update file
To fool Dell system to think that new FUU is the same version with its running version, I must use **Model Information** and **PFS Information** entries from current FUU version (1.12.2).
Then I can use other entries from older FUU version (BIOS v1.11.1, EC v1.11.1, etc.,).

I wrote [**Dell PFS BIOS Assembler**][5] to merge entries into a new FUU. Those entries are:
* **__exe_begin.bin**: the begging part of Dell FUU exe file
* **__exe_end.bin**: the ending part of Dell FUU exe file
* **Modem Information-1.12.2**: to fake BIOS payload version
* **FPS Information-1.12.2**: to have list of included entry GUIDs
* **BIOS-1.11.1**: BIOS entry of older Dell FUU, we will downgrade BIOS to this version
* **EC-1.11.1**: Embedded Controller of older Dell FUU, we will downgrade BIOS to this version
* other entries can use 1.12.2 version or 1.11.1 version (ME may not be downgraded)

![files.png](files.PNG)

```sh
python Dell_PFS_Assembler.py -f downgrade_to_1.11.1
```
After running the assembler, you will get new Dell FUU file as *__output.exe*. Rename it if needed.

### 3. Note before downgrading
Because downgrading can cause mismatched data problem, some functions on windows may not work normally. I had finger scanner problem after downgrading.
Therefore, you should think about the side effect before re-flashing.

### 4. Re-flash
Execute the new FUU file, or use BIOS Flash Programmer in BIOS menu. After downgrading, re-check your BIOS version and fix issues if needed.

[1]: https://www.win-raid.com/t3553f39-Guide-Unlock-Intel-Flash-Descriptor-Read-Write-Access-Permissions-for-SPI-Servicing.html
[2]: https://www.win-raid.com/t596f39-Intel-Management-Engine-Drivers-Firmware-amp-System-Tools.html
[3]: https://github.com/vuquangtrong
[4]: https://github.com/platomav/BIOSUtilities
[5]: https://github.com/vuquangtrong
