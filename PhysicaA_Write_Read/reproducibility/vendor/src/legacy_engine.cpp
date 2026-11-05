// Homogeneous-trust U/R/C process with triangle endorsement memory.
// Modes: 0 dynamic triangle, 1 neutral, 2 instantaneous, 3 frozen,
//        4 node compression, 5 edge compression.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <numeric>
#include <random>
#include <vector>
using std::vector;

struct Process {
 int n,m,f,mode; const int *ed,*tr,*sel;
 double b1,b2,T,lambda,mu=1;
 vector<int> x,te,nd,ec;
 vector<double> a,phi,lr,lc,nz,ez,ns,es;
 Process(int n_,int m_,int f_,const int* e,const int* t,const int* x0,
         const double* a0,double b1_,double b2_,double T_,double l,int md,const int* mask):
 n(n_),m(m_),f(f_),mode(md),ed(e),tr(t),sel(mask),b1(b1_),b2(b2_),T(T_),lambda(l),
 x(x0,x0+n),te(3*f),nd(n,0),ec(m,0),a(a0,a0+f),phi(f),lr(n),lc(n),
 nz(n,0),ez(m,0),ns(n),es(m) {
  if(mode>=4){
   for(int s=0;s<f;s++){
    for(int q=0;q<3;q++){int i=tr[3*s+q]; nd[i]++;nz[i]+=a[s];}
    for(int q=0;q<3;q++){
     int i=tr[3*s+q],j=tr[3*s+(q+1)%3]; if(i>j)std::swap(i,j);
     int lo=0,hi=m; while(lo<hi){int k=(lo+hi)/2;
      if(ed[2*k]<i || (ed[2*k]==i && ed[2*k+1]<j))lo=k+1;else hi=k;}
     te[3*s+q]=lo;ec[lo]++;ez[lo]+=a[s];
    }
   }
   for(int i=0;i<n;i++)if(nd[i])nz[i]/=nd[i];
   for(int e=0;e<m;e++)if(ec[e])ez[e]/=ec[e];
   reconstruct();
  }
  if(mode==1)std::fill(a.begin(),a.end(),0.);
 }
 void drive(){
  for(int s=0;s<f;s++){
   int nr=0,nc=0;for(int q=0;q<3;q++){nr+=x[tr[3*s+q]]==1;nc+=x[tr[3*s+q]]==2;}
   phi[s]=T*((nr>=2)-(nc>=2));
  }
 }
 void reconstruct(){
  if(mode==4)for(int s=0;s<f;s++)a[s]=(nz[tr[3*s]]+nz[tr[3*s+1]]+nz[tr[3*s+2]])/3;
  if(mode==5)for(int s=0;s<f;s++)a[s]=(ez[te[3*s]]+ez[te[3*s+1]]+ez[te[3*s+2]])/3;
 }
 void advance(double h){
  if(mode==0){double z=std::exp(-lambda*h);for(int s=0;s<f;s++)a[s]=phi[s]+(a[s]-phi[s])*z;}
  if(mode==2)a=phi;
  if(mode==4){
   std::fill(ns.begin(),ns.end(),0.);for(int s=0;s<f;s++)for(int q=0;q<3;q++)ns[tr[3*s+q]]+=phi[s];
   double z=std::exp(-lambda*h);for(int i=0;i<n;i++)if(nd[i])nz[i]=nz[i]*z+(1-z)*ns[i]/nd[i];reconstruct();
  }
  if(mode==5){
   std::fill(es.begin(),es.end(),0.);for(int s=0;s<f;s++)for(int q=0;q<3;q++)es[te[3*s+q]]+=phi[s];
   double z=std::exp(-lambda*h);for(int e=0;e<m;e++)if(ec[e])ez[e]=ez[e]*z+(1-z)*es[e]/ec[e];reconstruct();
  }
 }
 double rates(double u,bool bound=false){
  std::fill(lr.begin(),lr.end(),0.);for(int i=0;i<n;i++)lc[i]=sel[i]?u:0.;
  for(int e=0;e<m;e++){
   int i=ed[2*e],j=ed[2*e+1];
   lr[i]+=b1*T*(x[j]==1);lr[j]+=b1*T*(x[i]==1);
   lc[i]+=b1*T*(x[j]==2);lc[j]+=b1*T*(x[i]==2);
  }
  for(int s=0;s<f;s++){
   double ar=bound?std::max(a[s],phi[s]):a[s];
   double ac=bound?std::min(a[s],phi[s]):a[s];
   for(int q=0;q<3;q++){
    int i=tr[3*s+q],j=tr[3*s+(q+1)%3],k=tr[3*s+(q+2)%3];
    lr[i]+=b2*T*(1+ar)*(x[j]==1 && x[k]==1);
    lc[i]+=b2*T*(1-ac)*(x[j]==2 && x[k]==2);
   }
  }
  double tot=0;for(int i=0;i<n;i++)tot+=x[i]==0?lr[i]+lc[i]:(x[i]==1?lc[i]+mu:lr[i]+mu);
  return tot;
 }
 double memory(){
  double v=0;for(int s=0;s<f;s++)for(int q=0;q<3;q++){
   int i=tr[3*s+q],j=tr[3*s+(q+1)%3],k=tr[3*s+(q+2)%3];
   v+=a[s]*T*((x[i]!=1 && x[j]==1 && x[k]==1)+(x[i]==1 && x[j]==2 && x[k]==2));
  }return v/n;
 }
 void observe(double t,double* out){
  int r=0,c=0;for(int v:x){r+=v==1;c+=v==2;}
  out[0]=t;out[1]=double(r)/n;out[2]=double(c)/n;
  out[3]=std::accumulate(a.begin(),a.end(),0.)/std::max(1,f);out[4]=memory();
 }
};

extern "C" int simulate_selected(int n,int m,int f,const int* e,const int* tr,const int* x0,const int* selected,
 const double* a0,double beta1,double beta2,double trust,double lambda,double u,
 double D,double H,double dt,int mode,uint64_t seed,int nsamp,const double* sample_t,
 double* trajectory,int* xf,double* af,double* metrics,int exact){
 Process p(n,m,f,e,tr,x0,a0,beta1,beta2,trust,lambda,mode,selected);
 std::mt19937_64 gen(seed);std::uniform_real_distribution<double> unif(0,1);
 double t=0,end=D+H,peak=0,lastint=0,totalint=0,maxhaz=0;int si=0;
 bool off=false;double ob[5];
 auto record=[&](){while(si<nsamp && sample_t[si]<=t+1e-9){p.observe(sample_t[si],trajectory+5*si);si++;}};
 auto offcheck=[&](){if(!off && t>=D-1e-9){p.observe(t,ob);metrics[0]=ob[1];metrics[1]=ob[2];metrics[2]=ob[3];peak=ob[1];off=true;}};
 p.drive();if(mode==2)p.advance(0);record();offcheck();
 while(t<end-1e-10){
  p.drive();double bound=0,h;
  double boundary=end;if(t<D-1e-9)boundary=std::min(boundary,D);
  if(si<nsamp)boundary=std::min(boundary,sample_t[si]);
  // Split exactly at the final averaging window as well as interventions and observations.
  if(t<end-10-1e-9)boundary=std::min(boundary,end-10);
  double uu=t<D-1e-9?u:0;
  if(exact){bound=p.rates(uu,true);h=bound>0?-std::log(std::max(1e-300,unif(gen)))/bound:end-t;}
  else h=dt;
  bool candidate=exact && t+h<boundary-1e-12;
  h=std::min(h,boundary-t);if(h<1e-12){t=boundary;record();offcheck();continue;}
  double r=0;for(int v:p.x)r+=v==1;r/=n;
  if(t>=D-1e-9){totalint+=r*h;if(t>=end-10-1e-9)lastint+=r*h;}
  if(exact){
   p.advance(h);t+=h;
   if(candidate){
    p.rates(uu);double z=unif(gen)*bound;
    for(int i=0;i<n;i++){
     int old=p.x[i];double h1=old==0?p.lr[i]:(old==1?p.lc[i]:p.lr[i]);
     double h2=old==0?p.lc[i]:1.;
     if(z<h1){p.x[i]=old==0?1:(old==1?2:1);break;}
     z-=h1;if(z<h2){p.x[i]=old==0?2:0;break;}z-=h2;
    }
   }
  }else{
   p.advance(h/2);p.rates(uu);
   vector<int> next=p.x;
   for(int i=0;i<n;i++){
    int old=p.x[i];double h1=old==0?p.lr[i]:(old==1?p.lc[i]:p.lr[i]);
    double h2=old==0?p.lc[i]:1.;double hazard=h1+h2;maxhaz=std::max(maxhaz,h*hazard);
    double z=unif(gen);if(hazard>0 && z<-std::expm1(-h*hazard)){
     next[i]=(unif(gen)*hazard<h1)?(old==0?1:(old==1?2:1)):(old==0?2:0);
    }
   }
   p.advance(h/2);p.x.swap(next);t+=h;
  }
  if(off){double rr=0;for(int v:p.x)rr+=v==1;peak=std::max(peak,rr/n);}
  record();offcheck();
 }
 p.observe(t,ob);metrics[3]=peak;metrics[4]=H>0?lastint/std::min(10.,H):ob[1];
 metrics[5]=ob[1];metrics[6]=totalint;metrics[7]=maxhaz;metrics[8]=ob[3];
 std::copy(p.x.begin(),p.x.end(),xf);std::copy(p.a.begin(),p.a.end(),af);
 return si;
}
