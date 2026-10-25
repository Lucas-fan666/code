// State-independent marked Poisson proposals; R < U < C, a ordered in reverse.
// Classical graphical construction, specialized to signed relaxing face memory.
#include "rtc_engine.cpp"
#include <queue>

struct Proposal {double time;int channel;uint64_t count;};
struct Later {bool operator()(const Proposal& a,const Proposal& b)const {
    return a.time>b.time || (a.time==b.time && a.channel>b.channel);
}};
static double mark_uniform(uint64_t seed,int channel,uint64_t count) {
    uint64_t z=mix64(seed^mix64(uint64_t(channel)+UINT64_C(0x243f6a8885a308d3))
                     ^mix64(count+UINT64_C(0x13198a2e03707344)));
    return (double(z>>11)+0.5)*0x1.0p-53;
}

struct GraphicalTopology {
    int n,f;vector<vector<int>> neighbors,incident;const int* faces;
    vector<double> bounds;
    GraphicalTopology(int N,int M,int F,const int* e,const int* face,const double* p):
        n(N),f(F),neighbors(N),incident(N),faces(face),bounds(3*N) {
        for(int q=0;q<M;++q){int i=e[2*q],j=e[2*q+1];neighbors[i].push_back(j);neighbors[j].push_back(i);}
        for(int q=0;q<F;++q)for(int j=0;j<3;++j)incident[face[3*q+j]].push_back(q);
        for(int i=0;i<N;++i) {
            double upper=p[0]*p[2]*neighbors[i].size()+p[1]*p[2]*(1+p[2])*incident[i].size();
            bounds[3*i]=upper;bounds[3*i+1]=upper+p[4];bounds[3*i+2]=1.;
        }
    }
};

static double graphical_one(const GraphicalTopology& g,const int* x0,const double* a0,
        const double* p,const vector<int>& targets,uint64_t seed,uint64_t* diagnostics,uint64_t* work=nullptr) {
    vector<int> x(x0,x0+g.n);vector<char> target(g.n,0);
    for(int i:targets)target[i]=1;
    vector<double> a(a0,a0+g.f),last(g.f,0.),phi(g.f);
    auto drive=[&](int q){int r=0,c=0;for(int j=0;j<3;++j){int z=x[g.faces[3*q+j]];r+=z==1;c+=z==2;}
                          return p[2]*((r>=2)-(c>=2));};
    for(int q=0;q<g.f;++q)phi[q]=drive(q);
    auto memory=[&](int q,double t){return phi[q]+(a[q]-phi[q])*std::exp(-p[3]*(t-last[q]));};
    std::priority_queue<Proposal,vector<Proposal>,Later> queue;
    for(int k=0;k<3*g.n;++k)if(g.bounds[k]>0)queue.push({exponential(seed,k,0)/g.bounds[k],k,0});
    double t=0.,loss=0.,D=p[5],end=D+p[6];int rumor=0;for(int z:x)rumor+=z==1;
    uint64_t proposals=0,updates=0;
    while(!queue.empty()) {
        // R cannot reappear without an R donor; the remaining rumor loss is zero.
        if(rumor==0)break;
        Proposal q=queue.top();queue.pop();double time=std::min(end,q.time);
        loss+=double(rumor)/g.n*std::max(0.,time-std::max(t,D));t=time;
        if(q.time>=end)break;
        if(++proposals>50000000)return -1.;
        int i=q.channel/3,type=q.channel%3,dest=(type==0?1:(type==1?2:0));
        bool accepted=type==2;
        if(type!=2 && x[i]!=dest) {
            if(work)work[0]+=g.neighbors[i].size()+g.incident[i].size();
            double rate=(type==1 && target[i] && t<D ? p[4]:0.);
            for(int j:g.neighbors[i])if(x[j]==dest)rate+=p[0]*p[2];
            for(int f:g.incident[i]) {
                bool both=true;for(int j=0;j<3;++j){int v=g.faces[3*f+j];if(v!=i && x[v]!=dest)both=false;}
                if(both)rate+=p[1]*p[2]*(1+(type==0?1.:-1.)*memory(f,t));
            }
            if(rate>g.bounds[q.channel]+1e-8 || rate< -1e-8)return -1.;
            accepted=mark_uniform(seed,q.channel,q.count)*g.bounds[q.channel]<rate;
        }
        if(accepted && x[i]!=dest) {
            if(work)work[1]+=2*g.incident[i].size();
            for(int f:g.incident[i]){a[f]=memory(f,t);last[f]=t;}
            rumor+=(dest==1)-(x[i]==1);x[i]=dest;++updates;
            for(int f:g.incident[i])phi[f]=drive(f);
        }
        uint64_t next=q.count+1;
        queue.push({t+exponential(seed,q.channel,next)/g.bounds[q.channel],q.channel,next});
    }
    diagnostics[0]=proposals;diagnostics[1]=updates;
    return loss;
}

extern "C" int set_graphical_rollouts(int n,int m,int f,const int* e,const int* faces,
        const int* x,const double* a,const double* p,int nt,const int* targets,
        int reps,const uint64_t* seeds,double* loss,uint64_t* diagnostics) {
    GraphicalTopology graph(n,m,f,e,faces,p);vector<int> chosen(targets,targets+nt);
    for(int r=0;r<reps;++r) {
        loss[r]=graphical_one(graph,x,a,p,chosen,seeds[r],diagnostics+2*r);
        if(loss[r]<0)return 1;
    }
    return 0;
}

extern "C" int wp4_graphical_profile(int n,int m,int f,const int* e,const int* faces,
        const int* x,const double* a,const double* p,int nt,const int* targets,
        int reps,const uint64_t* seeds,double* loss,uint64_t* diagnostics) {
    GraphicalTopology graph(n,m,f,e,faces,p);vector<int>chosen(targets,targets+nt);
    for(int r=0;r<reps;++r){
        loss[r]=graphical_one(graph,x,a,p,chosen,seeds[r],diagnostics+4*r,diagnostics+4*r+2);
        if(loss[r]<0)return 1;
    }return 0;
}
