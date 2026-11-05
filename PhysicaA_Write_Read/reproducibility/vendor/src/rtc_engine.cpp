// Common reaction paths for the same PDMP. Not a new coupling principle.
// Every (node, transition) has a persistent operational-time Poisson clock.
#include "engine.cpp"
#include <limits>

static uint64_t mix64(uint64_t z) {
    z=(z^(z>>30))*UINT64_C(0xbf58476d1ce4e5b9);
    z=(z^(z>>27))*UINT64_C(0x94d049bb133111eb);return z^(z>>31);
}
static double exponential(uint64_t seed,int channel,uint64_t count) {
    uint64_t z=mix64(seed^mix64(uint64_t(channel)+UINT64_C(0x9e3779b97f4a7c15))
                       ^mix64(count+UINT64_C(0x632be59bd9b4e019)));
    double u=(double(z>>11)+0.5)*0x1.0p-53;
    return -std::log(u);
}
static double integrated(double c,double d,double lambda,double h) {
    return lambda>0 ? c*h+d*(-std::expm1(-lambda*h))/lambda : (c+d)*h;
}
static double invert_hazard(double c,double d,double lambda,double residual,double cap) {
    if (integrated(c,d,lambda,cap)<residual) return std::numeric_limits<double>::infinity();
    if (std::abs(d)<1e-14 || lambda==0) return residual/(c+d);
    double lo=0.,hi=cap,t=std::min(cap,residual/std::max(1e-12,c+d));
    for(int k=0;k<60;++k) {
        double f=integrated(c,d,lambda,t)-residual;
        if(std::abs(f)<1e-11*std::max(1.,residual))return t;
        if(f>0)hi=t;else lo=t;
        double rate=c+d*std::exp(-lambda*t);
        double next=t-f/std::max(1e-15,rate);
        t=(next>lo && next<hi) ? next : (lo+hi)/2.;
    }
    return (lo+hi)/2.;
}
static double rtc_one(int n,int m,int f,const int* edges,const int* faces,
        const int* x0,const double* a0,const double* p,const vector<int>& targets,
        uint64_t seed,uint64_t* event_count=nullptr) {
    Process s(n,m,f,edges,faces,x0,a0,p,false);
    int channels=6*n;vector<double> residual(channels),c(channels),d(channels),ar(n),ac(n),br(n),bc(n);
    vector<uint64_t> count(channels,0);
    for(int k=0;k<channels;++k)residual[k]=exponential(seed,k,0);
    const double D=p[5],end=D+p[6];double t=0.,loss=0.;int jumps=0;uint64_t events=0;
    int rumor=0;for(int z:s.x)rumor+=z==1;
    while(t<end-1e-12) {
        if(rumor==0)break;
        if(++jumps>10000000)return -1.;
        s.drive();std::fill(ar.begin(),ar.end(),0.);std::fill(ac.begin(),ac.end(),0.);
        std::fill(br.begin(),br.end(),0.);std::fill(bc.begin(),bc.end(),0.);
        if(t<D-1e-12)for(int v:targets)ac[v]=p[4];
        for(int e=0;e<m;++e) {
            int i=edges[2*e],j=edges[2*e+1];
            ar[i]+=s.b1*s.trust*(s.x[j]==1);ar[j]+=s.b1*s.trust*(s.x[i]==1);
            ac[i]+=s.b1*s.trust*(s.x[j]==2);ac[j]+=s.b1*s.trust*(s.x[i]==2);
        }
        for(int v=0;v<f;++v)for(int q=0;q<3;++q) {
            int i=faces[3*v+q],j=faces[3*v+(q+1)%3],k=faces[3*v+(q+2)%3];
            double b=s.b2*s.trust,delta=s.a[v]-s.phi[v];
            if(s.x[j]==1 && s.x[k]==1){ar[i]+=b*(1+s.phi[v]);br[i]+=b*delta;}
            if(s.x[j]==2 && s.x[k]==2){ac[i]+=b*(1-s.phi[v]);bc[i]-=b*delta;}
        }
        std::fill(c.begin(),c.end(),0.);std::fill(d.begin(),d.end(),0.);
        for(int i=0;i<n;++i) {
            int k=6*i;
            if(s.x[i]==0){c[k]=ar[i];d[k]=br[i];c[k+1]=ac[i];d[k+1]=bc[i];}
            if(s.x[i]==1){c[k+2]=ac[i];d[k+2]=bc[i];c[k+4]=1.;}
            if(s.x[i]==2){c[k+3]=ar[i];d[k+3]=br[i];c[k+5]=1.;}
        }
        double boundary=(t<D-1e-12 ? D:end),h=boundary-t;int fire=-1;
        for(int k=0;k<channels;++k)if(c[k]!=0. || d[k]!=0.) {
            double w=invert_hazard(c[k],d[k],s.lambda,residual[k],h);
            if(w<h){h=w;fire=k;}
        }
        if(t>=D-1e-12){int r=0;for(int v:s.x)r+=v==1;loss+=double(r)*h/n;}
        for(int k=0;k<channels;++k)residual[k]=std::max(0.,residual[k]-integrated(c[k],d[k],s.lambda,h));
        s.advance(h);t+=h;
        if(fire>=0){++events;static const int dest[6]={1,2,2,1,0,0};
            rumor+=(dest[fire%6]==1)-(s.x[fire/6]==1);s.x[fire/6]=dest[fire%6];
            residual[fire]=exponential(seed,fire,++count[fire]);}
    }
    if(event_count)*event_count=events;
    return loss;
}
extern "C" int rtc_rollouts(int n,int m,int f,const int* e,const int* s,
        const int* x,const double* a,const double* p,int target,
        int reps,const uint64_t* seeds,double* loss) {
    vector<int> chosen;if(target>=0)chosen.push_back(target);
    for(int r=0;r<reps;++r){loss[r]=rtc_one(n,m,f,e,s,x,a,p,chosen,seeds[r]);if(loss[r]<0)return 1;}
    return 0;
}
extern "C" int set_rtc_rollouts(int n,int m,int f,const int* e,const int* s,
        const int* x,const double* a,const double* p,int nt,const int* targets,
        int reps,const uint64_t* seeds,double* loss,uint64_t* event_count) {
    vector<int> chosen(targets,targets+nt);
    for(int r=0;r<reps;++r) {
        loss[r]=rtc_one(n,m,f,e,s,x,a,p,chosen,seeds[r],event_count+r);
        if(loss[r]<0)return 1;
    }
    return 0;
}
extern "C" double rtc_integrated(double c,double d,double lambda,double h){return integrated(c,d,lambda,h);}
extern "C" double rtc_inverse(double c,double d,double lambda,double residual,double cap){return invert_hazard(c,d,lambda,residual,cap);}
