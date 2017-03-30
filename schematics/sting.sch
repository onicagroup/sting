EESchema Schematic File Version 2
LIBS:power
LIBS:device
LIBS:transistors
LIBS:conn
LIBS:linear
LIBS:regul
LIBS:74xx
LIBS:cmos4000
LIBS:adc-dac
LIBS:memory
LIBS:xilinx
LIBS:microcontrollers
LIBS:dsp
LIBS:microchip
LIBS:analog_switches
LIBS:motorola
LIBS:texas
LIBS:intel
LIBS:audio
LIBS:interface
LIBS:digital-audio
LIBS:philips
LIBS:display
LIBS:cypress
LIBS:siliconi
LIBS:opto
LIBS:atmel
LIBS:contrib
LIBS:valves
LIBS:sting
LIBS:sting-cache
EELAYER 25 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 4
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Sheet
S 750  850  1950 1450
U 585ADC35
F0 "gun" 60
F1 "gun.sch" 60
$EndSheet
$Sheet
S 4300 2550 1550 1450
U 585B711C
F0 "raspi_interface" 60
F1 "raspi_interface.sch" 60
F2 "V_MAIN" I L 4300 2900 60 
F3 "V_CPU" I L 4300 3050 60 
F4 "GND" U L 4300 3350 60 
F5 "/PWR_OFF" O L 4300 3200 60 
$EndSheet
$Sheet
S 800  2750 1200 1050
U 585B18AF
F0 "power_control" 39
F1 "power_control.sch" 39
F2 "V_MAIN" O R 2000 2900 60 
F3 "V_CPU" O R 2000 3050 60 
F4 "GND" U R 2000 3350 60 
F5 "/PWR_OFF" I R 2000 3200 60 
$EndSheet
Wire Wire Line
	2000 2900 4300 2900
Wire Wire Line
	2000 3050 4300 3050
Wire Wire Line
	2000 3200 4300 3200
Wire Wire Line
	2000 3350 4300 3350
$EndSCHEMATC
