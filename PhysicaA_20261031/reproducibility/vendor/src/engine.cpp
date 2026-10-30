// Exact thinning for a piecewise-deterministic U/R/C process.
// Adapted from the supplied targeted_engine.cpp; no time discretization.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <random>
#include <vector>
using std::vector;

struct Process {
    int n, m, f;
    const int *edges, *faces;
    vector<int> x;
    vector<double> a, phi, lr, lc, node, edge;
    double b1, b2, trust, lambda;
    bool track;
    Process(int N, int M, int F, const int* E, const int* S,
            const int* X, const double* A, const double* p, bool tracking):
        n(N), m(M), f(F), edges(E), faces(S), x(X,X+N), a(A,A+F),
        phi(F), lr(N), lc(N), node(tracking ? 3*N : 0,0.),
        edge(tracking ? 9*M : 0,0.), b1(p[0]), b2(p[1]),
        trust(p[2]), lambda(p[3]), track(tracking) {}
    void drive() {
        for (int s=0;s<f;++s) {
            int r=0,c=0;
            for (int j=0;j<3;++j) { int v=x[faces[3*s+j]]; r+=v==1; c+=v==2; }
            phi[s]=trust*((r>=2)-(c>=2));
        }
    }
    void advance(double h) {
        double z=std::exp(-lambda*h), w=-std::expm1(-lambda*h);
        for (int s=0;s<f;++s) a[s]=z*a[s]+w*phi[s];
        if (!track) return;
        for (double& v:node) v*=z;
        for (double& v:edge) v*=z;
        for (int i=0;i<n;++i) node[3*i+x[i]]+=w;
        for (int e=0;e<m;++e) edge[9*e+3*x[edges[2*e]]+x[edges[2*e+1]]]+=w;
    }
    double rates(int target, double u, bool upper, const vector<int>* targets=nullptr) {
        std::fill(lr.begin(),lr.end(),0.);
        std::fill(lc.begin(),lc.end(),0.);
        if (target>=0) lc[target]=u;
        if (targets) for (int v:*targets) lc[v]=u;
        for (int e=0;e<m;++e) {
            int i=edges[2*e],j=edges[2*e+1];
            lr[i]+=b1*trust*(x[j]==1); lr[j]+=b1*trust*(x[i]==1);
            lc[i]+=b1*trust*(x[j]==2); lc[j]+=b1*trust*(x[i]==2);
        }
        for (int s=0;s<f;++s) {
            double ar=upper ? std::max(a[s],phi[s]) : a[s];
            double ac=upper ? std::min(a[s],phi[s]) : a[s];
            for (int q=0;q<3;++q) {
                int i=faces[3*s+q], j=faces[3*s+(q+1)%3],k=faces[3*s+(q+2)%3];
                lr[i]+=b2*trust*(1+ar)*(x[j]==1 && x[k]==1);
                lc[i]+=b2*trust*(1-ac)*(x[j]==2 && x[k]==2);
            }
        }
        double total=0.;
        for (int i=0;i<n;++i)
            total+=(x[i]==0 ? lr[i]+lc[i] : (x[i]==1 ? lc[i]+1. : lr[i]+1.));
        return total;
    }
};

static double simulate(int n,int m,int f,const int* edges,const int* faces,
        const int* x0,const double* a0,const double* p,int target,uint64_t seed,
        int* xf,double* af,double* node,double* edge,double* diagnostics,bool track,
        const vector<int>* targets=nullptr, bool antithetic=false) {
    Process s(n,m,f,edges,faces,x0,a0,p,track);
    std::mt19937_64 gen(seed);
    std::uniform_real_distribution<double> uniform(0.,1.);
    auto draw=[&](){double v=uniform(gen);return antithetic ? 1.-v : v;};
    const double D=p[5],end=D+p[6];
    double t=0., loss=0.; uint64_t proposals=0, jumps=0;
    while (t<end-1e-12) {
        // Loss-only calls may stop at rumor extinction. Histories still return
        // the full endpoint state and memory, so they must run to the horizon.
        if(!track && !xf && std::none_of(s.x.begin(),s.x.end(),[](int z){return z==1;}))break;
        s.drive();
        double boundary=(t<D-1e-12 ? D : end);
        double u=(t<D-1e-12 ? p[4] : 0.);
        double upper=s.rates(target,u,true,targets);
        double h=upper>0. ? -std::log(std::max(1e-300,draw()))/upper : end-t;
        bool candidate=t+h<boundary-1e-12;
        h=std::min(h,boundary-t);
        if (h<1e-14) {t=boundary; continue;}
        if (t>=D-1e-12) {
            int r=0; for (int v:s.x) r+=v==1;
            loss+=double(r)*h/n;
        }
        s.advance(h); t+=h;
        if (candidate) {
            ++proposals;
            double actual=s.rates(target,u,false,targets);
            if (actual>upper+1e-8) return -1.; // invalid dominating rate
            double z=draw()*upper;
            for (int i=0;i<n;++i) {
                int old=s.x[i];
                double h1=(old==0 ? s.lr[i] : (old==1 ? s.lc[i] : s.lr[i]));
                double h2=(old==0 ? s.lc[i] : 1.);
                if (z<h1) {s.x[i]=(old==0 ? 1 : (old==1 ? 2 : 1)); ++jumps; break;}
                z-=h1;
                if (z<h2) {s.x[i]=(old==0 ? 2 : 0); ++jumps; break;}
                z-=h2;
            }
        }
    }
    if (xf) std::copy(s.x.begin(),s.x.end(),xf);
    if (af) std::copy(s.a.begin(),s.a.end(),af);
    if (track) {
        std::copy(s.node.begin(),s.node.end(),node);
        std::copy(s.edge.begin(),s.edge.end(),edge);
    }
    if (diagnostics) {diagnostics[0]=double(proposals); diagnostics[1]=double(jumps);}
    return loss;
}

extern "C" int history(int n,int m,int f,const int* e,const int* s,
        const int* x,const double* a,const double* p,int target,uint64_t seed,
        int* xf,double* af,double* node,double* edge) {
    return simulate(n,m,f,e,s,x,a,p,target,seed,xf,af,node,edge,nullptr,true)>=0 ? 0 : 1;
}

extern "C" int rollouts(int n,int m,int f,const int* e,const int* s,
        const int* x,const double* a,const double* p,int target,
        int reps,const uint64_t* seeds,double* loss) {
    for (int r=0;r<reps;++r) {
        loss[r]=simulate(n,m,f,e,s,x,a,p,target,seeds[r],nullptr,nullptr,nullptr,nullptr,nullptr,false);
        if (loss[r]<0) return 1;
    }
    return 0;
}

// A set intervention supplies the same per-node intensity p[4] to every target.
extern "C" int set_thinning_rollouts(int n,int m,int f,const int* e,const int* s,
        const int* x,const double* a,const double* p,int nt,const int* targets,
        int reps,const uint64_t* seeds,double* loss) {
    vector<int> chosen(targets,targets+nt);
    for(int r=0;r<reps;++r) {
        loss[r]=simulate(n,m,f,e,s,x,a,p,-1,seeds[r],nullptr,nullptr,nullptr,nullptr,
                         nullptr,false,&chosen);
        if(loss[r]<0)return 1;
    }
    return 0;
}

// A generic antithetic baseline: complement EVERY uniform on a tape. Both
// members have the same marginal law. Charge both paths, not one pair as one.
extern "C" int wp3_thinning_rollouts(int n,int m,int f,const int* e,const int* s,
        const int* x,const double* a,const double* p,int nt,const int* targets,
        int reps,const uint64_t* seeds,double* loss,int anti,uint64_t* counts) {
    vector<int> chosen(targets,targets+nt);
    for(int r=0;r<reps;++r){
        double di[2]={0.,0.};
        loss[r]=simulate(n,m,f,e,s,x,a,p,-1,seeds[r],nullptr,nullptr,nullptr,nullptr,
                         di,false,&chosen,anti!=0);
        counts[2*r]=uint64_t(di[0]);counts[2*r+1]=uint64_t(di[1]);
        if(loss[r]<0)return 1;
    }
    return 0;
}
