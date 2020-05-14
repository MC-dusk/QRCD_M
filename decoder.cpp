#include <iostream>
#include <cstdio>
#include <windows.h>
#include <cassert>
using namespace std;

const int BUF_SIZE=1024*1024;

char KEY1[]="!@#)(NHLiuy*$%^&";
char KEY2[]="123ZXC!@#)(*$%^&";
char KEY3[]="!@#)(*$%^&abcDEF";

void print_bin2hex(char *buf,int len) {
	for(int i=0;i<len;i++) {
		unsigned int hex=buf[i];
		printf("%x%x",(hex/16)%16,hex%16);
	}
	puts("");
}

char content[BUF_SIZE];

int parse_hex(int c) {
	if(c>='0' && c<='9') return (c-'0');
	else if(c>='a' && c<='f') return (c-'a'+10);
	else if(c>='A' && c<='F') return (c-'A'+10);
	else return -1;
}

int read_hex_content() { // return size
	int sz=0;
	while(true) {
		int c=parse_hex(getchar());
		int d=parse_hex(getchar());
		if(c==-1 || d==-1) break;
		content[sz++]=c*16+d;
	}
	return sz;
}

int main() {
    auto lib=LoadLibrary("QQMusicCommon.dll");
    if(!lib) throw 1;

    auto func_ddes=(void (*)(char *,char *,int))GetProcAddress(lib,"?Ddes@qqmusic@@YAHPAE0H@Z");
    auto func_des=(void (*)(char *,char *,int))GetProcAddress(lib,"?des@qqmusic@@YAHPAE0H@Z");
    
    //FILE *fin=fopen("kiseki.qrc","rb");
    //if(!fin) throw 1;
    //auto sz=fread(content,1,BUF_SIZE,fin);
    //assert(sz<BUF_SIZE);
    
    auto sz=read_hex_content();
    
    //printf("size=%d\n",sz);
    //printf("orig: ");
    //print_bin2hex(content,10);
    
    func_ddes(content,KEY1,sz);
    func_des(content,KEY2,sz);
    func_ddes(content,KEY3,sz);
    
    //printf("after ");
    //print_bin2hex(content,10);
    
    //FILE *fout=fopen("kiseki_out.qrc","wb");
    //fwrite(content,1,sz,fout);
    
    print_bin2hex(content,sz);
    
    return 0;
}
