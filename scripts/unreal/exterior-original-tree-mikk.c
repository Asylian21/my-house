/* R24 source-only MikkTSpace callback adapter. No Unreal runtime or asset API. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include "mikktspace.h"

typedef struct {
    unsigned char *source;
    size_t vertices, index_count, po, no, uo, io, ps, ns, us, is;
    int index_width;
    float su, sv, ou, ov;
    float *tangents;
    unsigned char *seen;
    size_t callbacks, conflicts, sign_conflicts;
    double max_difference;
} Data;

static uint32_t vertex(const Data *d, int face, int corner) {
    const unsigned char *p=d->source+d->io+((size_t)face*3+corner)*d->is;
    uint32_t i=0;
    if(d->index_width==2){uint16_t v;memcpy(&v,p,2);i=v;}else memcpy(&i,p,4);
    if(i>=d->vertices){fprintf(stderr,"Source index outside original vertices\n");exit(2);}return i;
}
static float value(const unsigned char *p){float v;memcpy(&v,p,4);return v;}
static int faces(const SMikkTSpaceContext *c){return (int)(((Data*)c->m_pUserData)->index_count/3);}
static int corners(const SMikkTSpaceContext *c,int face){(void)c;(void)face;return 3;}
static void position(const SMikkTSpaceContext *c,float p[],int f,int v){Data*d=c->m_pUserData;const unsigned char*q=d->source+d->po+vertex(d,f,v)*d->ps;for(int i=0;i<3;i++)p[i]=value(q+i*4);}
static void normal(const SMikkTSpaceContext *c,float p[],int f,int v){Data*d=c->m_pUserData;const unsigned char*q=d->source+d->no+vertex(d,f,v)*d->ns;for(int i=0;i<3;i++)p[i]=value(q+i*4);}
static void uv(const SMikkTSpaceContext *c,float p[],int f,int v){Data*d=c->m_pUserData;const unsigned char*q=d->source+d->uo+vertex(d,f,v)*d->us;p[0]=value(q)*d->su+d->ou;p[1]=value(q+4)*d->sv+d->ov;}
static void tangent(const SMikkTSpaceContext *c,const float t[],float sign,int f,int v){
    Data*d=c->m_pUserData;uint32_t i=vertex(d,f,v);float out[4]={t[0],t[1],t[2],sign};d->callbacks++;
    if(!d->seen[i]){memcpy(d->tangents+i*4,out,16);d->seen[i]=1;return;}
    if(memcmp(d->tangents+i*4,out,16)!=0){d->conflicts++;for(int k=0;k<4;k++){double diff=fabs((double)d->tangents[i*4+k]-out[k]);if(diff>d->max_difference)d->max_difference=diff;}if(d->tangents[i*4+3]!=sign)d->sign_conflicts++;}
}
int main(int argc,char**argv){
    /* source, NV, NI, P,N,UV,I offsets; P,N,UV,I strides; I width;
       UV scale/offset; tangent output; evidence output */
    if(argc!=19){fprintf(stderr,"Expected18 explicitly typed source arguments\n");return 2;}
    FILE*in=fopen(argv[1],"rb");if(!in)return 2;fseek(in,0,SEEK_END);long bytes=ftell(in);rewind(in);
    Data d={0};d.source=malloc((size_t)bytes);if(!d.source)return 2;if(fread(d.source,1,(size_t)bytes,in)!=(size_t)bytes)return 2;fclose(in);
    d.vertices=strtoull(argv[2],NULL,10);d.index_count=strtoull(argv[3],NULL,10);d.po=strtoull(argv[4],NULL,10);d.no=strtoull(argv[5],NULL,10);d.uo=strtoull(argv[6],NULL,10);d.io=strtoull(argv[7],NULL,10);
    d.ps=strtoull(argv[8],NULL,10);d.ns=strtoull(argv[9],NULL,10);d.us=strtoull(argv[10],NULL,10);d.is=strtoull(argv[11],NULL,10);d.index_width=atoi(argv[12]);
    d.su=strtof(argv[13],NULL);d.sv=strtof(argv[14],NULL);d.ou=strtof(argv[15],NULL);d.ov=strtof(argv[16],NULL);
    if(d.index_count%3||d.vertices==0||(d.index_width!=2&&d.index_width!=4)||d.po+(d.vertices-1)*d.ps+12>(size_t)bytes||d.no+(d.vertices-1)*d.ns+12>(size_t)bytes||d.uo+(d.vertices-1)*d.us+8>(size_t)bytes||d.io+(d.index_count-1)*d.is+d.index_width>(size_t)bytes)return 2;
    d.tangents=calloc(d.vertices*4,sizeof(float));d.seen=calloc(d.vertices,1);if(!d.tangents||!d.seen)return 2;
    SMikkTSpaceInterface iface={0};iface.m_getNumFaces=faces;iface.m_getNumVerticesOfFace=corners;iface.m_getPosition=position;iface.m_getNormal=normal;iface.m_getTexCoord=uv;iface.m_setTSpaceBasic=tangent;
    SMikkTSpaceContext context={&iface,&d};int ok=genTangSpaceDefault(&context);size_t unseen=0;
    for(size_t i=0;i<d.vertices;i++)if(!d.seen[i])unseen++;
    FILE*report=fopen(argv[18],"wx");if(!report)return 2;
    fprintf(report,"{\"mikkSucceeded\":%s,\"sourceVertices\":%zu,\"sourceTriangles\":%zu,\"cornerCallbacks\":%zu,\"sharedIndexBinary32CornerConflicts\":%zu,\"sharedIndexHandednessConflicts\":%zu,\"maximumSharedIndexDifference\":%.17g,\"unreferencedVertices\":%zu,\"nativeOrGpuExecuted\":false}\n",ok?"true":"false",d.vertices,d.index_count/3,d.callbacks,d.conflicts,d.sign_conflicts,d.max_difference,unseen);fclose(report);
    /* Refuse incompatible corner frames; never split/reindex original vertices. */
    if(!ok||d.conflicts||unseen){free(d.source);free(d.tangents);free(d.seen);return 3;}
    FILE*out=fopen(argv[17],"wbx");if(!out)return 2;size_t written=fwrite(d.tangents,16,d.vertices,out);fclose(out);
    free(d.source);free(d.tangents);free(d.seen);return written==d.vertices?0:2;
}
