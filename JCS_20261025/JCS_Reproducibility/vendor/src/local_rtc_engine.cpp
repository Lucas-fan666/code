// Incremental common reaction paths. Same six clocks and tape as rtc_engine.cpp.
// Indexed heap stores exactly 6*n channel entries, including inactive clocks.
#include "rtc_engine.cpp"
#include <algorithm>

struct IndexedHeap {
    vector<int> heap,pos;vector<double> time;
    IndexedHeap(int n):heap(n),pos(n),time(n,std::numeric_limits<double>::infinity()) {
        for(int i=0;i<n;++i)heap[i]=pos[i]=i;
    }
    bool less(int a,int b)const{return time[a]<time[b] || (time[a]==time[b] && a<b);}
    void swap_at(int a,int b){std::swap(heap[a],heap[b]);pos[heap[a]]=a;pos[heap[b]]=b;}
    void set(int ch,double value){
        time[ch]=value;int i=pos[ch];
        while(i && less(heap[i],heap[(i-1)/2])){swap_at(i,(i-1)/2);i=(i-1)/2;}
        while(true){int l=2*i+1,r=l+1,j=i;
            if(l<int(heap.size()) && less(heap[l],heap[j]))j=l;
            if(r<int(heap.size()) && less(heap[r],heap[j]))j=r;
            if(j==i)break;swap_at(i,j);i=j;}
    }
    int top()const{return heap[0];}
};

struct LocalTopology {
    int n,f;const int* faces;vector<vector<int>> neighbors,incident;
    LocalTopology(int N,int M,int F,const int* e,const int* ff):
        n(N),f(F),faces(ff),neighbors(N),incident(N){
        for(int q=0;q<M;++q){int i=e[2*q],j=e[2*q+1];neighbors[i].push_back(j);neighbors[j].push_back(i);}
        for(int q=0;q<F;++q)for(int j=0;j<3;++j)incident[ff[3*q+j]].push_back(q);
    }
};

static double local_rtc_one(const LocalTopology& g,const int* x0,const double* a0,
        const double* p,const vector<int>& targets,uint64_t seed,uint64_t* diag){
    const int nc=6*g.n;const double inf=std::numeric_limits<double>::infinity();
    const double lambda=p[3],D=p[5],end=D+p[6],pair=p[0]*p[2],face=p[1]*p[2];
    vector<int>x(x0,x0+g.n),stamp(g.n,-1);vector<char>target(g.n,0);
    for(int v:targets)target[v]=1;
    vector<double>a(a0,a0+g.f),phi(g.f),flast(g.f,0.),clast(g.n,0.);
    vector<double>rc(g.n,0.),rd(g.n,0.),cc(g.n,0.),cd(g.n,0.);
    vector<double>res(nc),c(nc,0.),d(nc,0.),last(nc,0.);
    vector<uint64_t>count(nc,0);IndexedHeap queue(nc);
    auto drive=[&](int q){int r=0,z=0;for(int j=0;j<3;++j){r+=x[g.faces[3*q+j]]==1;z+=x[g.faces[3*q+j]]==2;}
        return p[2]*((r>=2)-(z>=2));};
    auto add_face=[&](int q,double sign){
        for(int b=0;b<3;++b){int i=g.faces[3*q+b],j=g.faces[3*q+(b+1)%3],k=g.faces[3*q+(b+2)%3];
            if(x[j]==1 && x[k]==1){rc[i]+=sign*face*(1+phi[q]);rd[i]+=sign*face*(a[q]-phi[q]);}
            if(x[j]==2 && x[k]==2){cc[i]+=sign*face*(1-phi[q]);cd[i]-=sign*face*(a[q]-phi[q]);}
        }
    };
    for(int i=0;i<g.n;++i)for(int j:g.neighbors[i]){rc[i]+=pair*(x[j]==1);cc[i]+=pair*(x[j]==2);}
    for(int q=0;q<g.f;++q){phi[q]=drive(q);add_face(q,1.);}
    for(int ch=0;ch<nc;++ch)res[ch]=exponential(seed,ch,0);
    uint64_t events=0,channel_refreshes=0,incidence_visits=0;
    auto accrue=[&](int i,double t){
        double dt=t-clast[i],decay=std::exp(-lambda*dt);rd[i]*=decay;cd[i]*=decay;clast[i]=t;
        for(int b=0;b<6;++b){int ch=6*i+b;
            res[ch]=std::max(0.,res[ch]-integrated(c[ch],d[ch],lambda,t-last[ch]));last[ch]=t;}
    };
    auto refresh=[&](int i,double t,bool active){
        double cor=cc[i]+(active && target[i]?p[4]:0.);
        for(int b=0;b<6;++b){int ch=6*i+b;c[ch]=d[ch]=0.;
            if((b==0 && x[i]==0)||(b==3 && x[i]==2)){c[ch]=rc[i];d[ch]=rd[i];}
            if((b==1 && x[i]==0)||(b==2 && x[i]==1)){c[ch]=cor;d[ch]=cd[i];}
            if((b==4 && x[i]==1)||(b==5 && x[i]==2))c[ch]=1.;
            // Tiny cancellation errors cannot create negative hazards.
            if(std::abs(c[ch])<1e-13)c[ch]=0.;if(std::abs(d[ch])<1e-13)d[ch]=0.;
            if(c[ch]+d[ch]<-1e-8)return false;
            double dt=(c[ch]!=0. || d[ch]!=0.)?invert_hazard(c[ch],d[ch],lambda,res[ch],end-t):inf;
            queue.set(ch,t+dt);++channel_refreshes;
        }return true;
    };
    for(int i=0;i<g.n;++i)if(!refresh(i,0.,D>0.))return -2.;
    int rumor=0;for(int z:x)rumor+=z==1;double t=0.,loss=0.;bool crossed=D<=0.;int epoch=0;
    while(t<end-1e-12 && rumor>0){
        int fire=queue.top();double next=queue.time[fire];
        if(!crossed && D<=next && D<end){
            t=D;for(int i:targets){accrue(i,t);if(!refresh(i,t,false))return -2.;}crossed=true;continue;
        }
        double stop=std::min(next,end);loss+=double(rumor)/g.n*std::max(0.,stop-std::max(t,D));t=stop;
        if(next>=end)break;if(++events>10000000)return -1.;
        int v=fire/6;static const int dest[6]={1,2,2,1,0,0};int old=x[v],to=dest[fire%6];
        vector<int>affected; ++epoch;
        auto touch=[&](int i){if(stamp[i]!=epoch){stamp[i]=epoch;affected.push_back(i);}};
        touch(v);for(int j:g.neighbors[v]){touch(j);++incidence_visits;}
        for(int q:g.incident[v]){for(int b=0;b<3;++b)touch(g.faces[3*q+b]);++incidence_visits;}
        for(int i:affected)accrue(i,t);
        for(int q:g.incident[v]){a[q]=phi[q]+(a[q]-phi[q])*std::exp(-lambda*(t-flast[q]));flast[q]=t;add_face(q,-1.);}
        for(int j:g.neighbors[v]){rc[j]+=pair*((to==1)-(old==1));cc[j]+=pair*((to==2)-(old==2));}
        rumor+=(to==1)-(old==1);x[v]=to;
        for(int q:g.incident[v]){phi[q]=drive(q);add_face(q,1.);}
        res[fire]=exponential(seed,fire,++count[fire]);
        for(int i:affected)if(!refresh(i,t,!crossed))return -2.;
    }
    diag[0]=events;diag[1]=channel_refreshes;diag[2]=incidence_visits;return loss;
}

extern "C" int set_local_rtc_rollouts(int n,int m,int f,const int* e,const int* faces,
        const int* x,const double* a,const double* p,int nt,const int* targets,
        int reps,const uint64_t* seeds,double* loss,uint64_t* diag){
    LocalTopology graph(n,m,f,e,faces);vector<int>chosen(targets,targets+nt);
    for(int r=0;r<reps;++r){loss[r]=local_rtc_one(graph,x,a,p,chosen,seeds[r],diag+3*r);if(loss[r]<0)return 1;}
    return 0;
}
