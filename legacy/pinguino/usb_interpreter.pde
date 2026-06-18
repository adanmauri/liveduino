/*
 * Copyright (c) 2014 Adán Mauri Ungaro <adan.mauri@gmail.com>
 *
 * This file is part of FrameDuino. FrameDuino is free software; you can
 * redistribute it and/or modify it under the terms of the GNU General Public
 * License as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.  See the file
 * COPYING included with this distribution for more information.
 */

#define __pins__ 21
#define __ilgth__ 21

char read[__ilgth__], *block;
char send[__ilgth__];
int par1, c;

char *strtok(char *str, char *control) {
//Written By -  Sandeep Dutta . sandeep.dutta@usa.net (1999)
static  char * s; register char * s1; if (str)s = str; if (!s)return NULL;
while (*s) { if (strchr(control,*s))s++; else break;}
s1 = s ; while (*s) { if (strchr(control,*s)) {*s++ = '\0'; return s1 ;} s++ ;}
s = NULL;  if (*s1)return s1; else return NULL; }

void fd_strcpy(char dest[], const char source[]) {
int i = 0;while (1) { dest[i] = source[i];if (dest[i] == '\0') break; i++; }
}

int fd_strcmp(char *src1, char *src2, int n) {
int i=0; while (1) {
if ( ((src1[i]=='\0') || (src2[i]=='\0')) && ( i == n )) return 0;
if(src1[i] > src2[i]) return 1; if(src1[i] < src2[i]) return -1; i++;}
}

int fd_atoi(char *str) {
int i, res = 0; for (i = 0; str[i] != '\0'; ++i) res = res*10 + str[i] - '0'; return res;
}

void fd_itoa(char str[], int num) {
int i, c = 0, aux=num; int dig;
while (aux != 0) {aux = (aux / 10);c++; }
str[c] = '\0'; 
for (i = c; i > 0; i--) {dig = num % 10;num = (num / 10);str[i-1] = dig + 48;}  
}

int fd_strlen(char *str) {
int i = 0; while(1){if (str[i]=='\0') break;i++;}return i;
}

void setup() {}

void read_instruction() {
unsigned char buffer[__ilgth__];
  unsigned char receivedbyte=0;
  if(USB.available())
    receivedbyte = USB.read(buffer);
  buffer[receivedbyte] = 0;
  if (receivedbyte > 0)
    fd_strcpy(read, buffer);
}
    
void loop() {

read_instruction();
fd_strcpy(send, "");
c=0;
// pinMode
if (fd_strcmp(read, "pinMode", 7)==0){
  for (block = strtok(read,"("); block != NULL; block = strtok(NULL, ",") ){ 
    switch (c){
      case 1:
        par1=fd_atoi(block);
        break;
      case 2:
        if (fd_strcmp(block, "INPUT", 5)==0)       pinMode(par1,INPUT);
        else if (fd_strcmp(block, "OUTPUT", 6)==0) pinMode(par1,OUTPUT);
        break;
    } 
    c++;
  }
}
// digitalWrite
else if (fd_strcmp(read, "digitalWrite", 12)==0){
  for (block = strtok(read,"("); block != NULL; block = strtok(NULL, ",") ){
    switch (c){
      case 1:
        par1=fd_atoi(block);
        break;
      case 2:
        if (fd_strcmp(block, "HIGH", 4)==0)     digitalWrite(par1,HIGH);
        else if (fd_strcmp(block, "LOW", 3)==0) digitalWrite(par1,LOW);
        break;
    }
    c++;
  }
}
// analogWrite
else if (fd_strcmp(read, "analogWrite", 11)==0){
  for (block = strtok(read,"("); block != NULL; block = strtok(NULL, ",") ){
    switch (c){
      case 1:
        par1=fd_atoi(block);
        break;
      case 2:
        analogWrite(par1,fd_atoi(block));
        break;
     } 
     c++;
  }
}
// digitalRead
else if (fd_strcmp(read, "digitalRead", 11)==0){
  for (block = strtok(read,"("); block != NULL; block = strtok(NULL, ")") ){
    switch (c){
      case 1:
        USB.write(digitalRead(fd_atoi(block)), fd_strlen(send));
        break;
    } 
    c++;
  }
}
// analogRead
else if (fd_strcmp(read, "analogRead", 10)==0){
  for (block = strtok(read,"("); block != NULL; block = strtok(NULL, ")") ){
    switch (c){
        case 1:
          fd_itoa(send,analogRead(fd_atoi(block)));
          USB.write(send, fd_strlen(send));
          break;
    } 
    c++;
  }
}
// eepromRead
else if (fd_strcmp(read, "eepromRead", 10)==0){
  for (block = strtok(read,"("); block != NULL; block = strtok(NULL, ")") ){
    switch (c){
      case 1:
        fd_itoa(send,analogRead(fd_atoi(block)));
        USB.write(send, fd_strlen(send));
        break;
    } 
    c++;
  }
}
// eepromWrite
else if (fd_strcmp(read, "eepromWrite", 11)==0){
  for (block = strtok(read,"("); block != NULL; block = strtok(NULL, ",") ){
    switch (c){
      case 1:
        par1=fd_atoi(block);
        break;
      case 2:
        block = strtok(block,")");
        EEPROM.write(par1, fd_atoi(block));
        break;
    } 
    c++;
  }
}
// delay
else if (fd_strcmp(read, "delay", 5)==0){
  for (block = strtok(read,"("); block != NULL; block = strtok(NULL, ")") ){
    switch (c){
      case 1:
        delay(fd_atoi(block));
        break;
    } 
    c++;
  }
}
// delayMicroseconds
else if (fd_strcmp(read, "delayMicroseconds", 17)==0){
  for (block = strtok(read,"("); block != NULL; block = strtok(NULL, ")") ){
    switch (c){
      case 1:
        delayMicroseconds(fd_atoi(block));
        break;
    } 
    c++;
  }
}
// allOutput
else if (fd_strcmp(read, "allOutput", 9)==0){
  for (c=0;c<=__pins__;c++){
    pinMode(c,OUTPUT);
    digitalWrite(c,LOW);
  }
}
// allInput
else if (fd_strcmp(read, "allInput", 8)==0){
  for (c=0;c<=__pins__;c++)
    pinMode(c,INPUT);
}
// allHigh
else if (fd_strcmp(read, "allHigh", 7)==0){
  for (c=0;c<=__pins__;c++){
    pinMode(c,OUTPUT);
    digitalWrite(c,HIGH);
  }
}
// allLow
else if (fd_strcmp(read, "allLow", 6)==0){
  for (c=0;c<=__pins__;c++){
    pinMode(c,OUTPUT);
    digitalWrite(c,LOW);
   }
}
// reset
else if (fd_strcmp(read, "reset", 5)==0)
  reset();
}