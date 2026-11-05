// Exact marked reset simulation on uniform hyperedges. Parameters are synthetic.
#include "../vendor/src/graphical_engine.cpp"
struct HyperTopology {
 int n,f,q; const int* face; const double* weight;
 vector<vector<int>> neighbors,incident; vector<double> bounds;
 HyperTopology(int N,int M,int F,int Q,const int* e,const int* ff,const double* w,const double* p):n(N),f(F),q(Q),face(ff),weight(w),neighbors(N),incident(N),bounds(3*N){
  for(int j=0;j<M;++j){neighbors[e[2*j]].push_back(e[2*j+1]);neighbors[e[2*j+1]].push_back(e[2*j]);}
  for(int j=0;j<F;++j)for(int k=0;k<Q;++k)incident[ff[Q*j+k]].push_back(j);
  for(int i=0;i<N;++i){double fw=0;for(int j:incident[i])fw+=weight[j];double u=p[0]*p[2]*neighbors[i].size()+p[1]*p[2]*(1+p[2])*fw;bounds[3*i]=u;bounds[3*i+1]=u+p[4];bounds[3*i+2]=1;}
 }
};
static double hyper_path(const HyperTopology& g,const int* x0,const double* a0,const double* p,const vector<int>& targets,uint64_t seed,int ng,const double* grid,double* trace,int* xe,double* ae){
 vector<int>x(x0,x0+g.n);vector<char>target(g.n,0);for(int i:targets)target[i]=1;
 vector<double>a(a0,a0+g.f),last(g.f,0),phi(g.f);
 auto drive=[&](int f){int r=0,c=0;for(int k=0;k<g.q;++k){int z=x[g.face[g.q*f+k]];r+=z==1;c+=z==2;}return p[7]==1?p[2]*double(r-c)/g.q:p[2]*((r>=g.q/2+1)-(c>=g.q/2+1));};
 for(int f=0;f<g.f;++f)phi[f]=drive(f);
 auto memory=[&](int f,double t){return phi[f]+(a[f]-phi[f])*std::exp(-p[3]*(t-last[f]));};
 int obs=0,nr=0,nc=0;for(int z:x){nr+=z==1;nc+=z==2;}
 auto record=[&](double t){trace[2*obs]=double(nr)/g.n;double av=0;for(int f=0;f<g.f;++f)av+=memory(f,t);trace[2*obs+1]=g.f?av/g.f:0.;++obs;};
 std::priority_queue<Proposal,vector<Proposal>,Later>queue;for(int k=0;k<3*g.n;++k)if(g.bounds[k]>0)queue.push({exponential(seed,k,0)/g.bounds[k],k,0});
 double t=0,loss=0,D=p[5],end=D+p[6];uint64_t proposals=0;
 while(!queue.empty()){
  auto z=queue.top();queue.pop();double until=std::min(end,z.time);
  while(obs<ng && grid[obs]<=until)record(grid[obs]);
  loss+=double(nr)/g.n*std::max(0.,until-std::max(t,D));t=until;if(z.time>=end)break;
  if(++proposals>50000000)return -1.;
  int i=z.channel/3,type=z.channel%3,dest=type==0?1:(type==1?2:0);bool accept=type==2;
  if(type!=2 && x[i]!=dest){double rate=type==1 && target[i] && t<D?p[4]:0;
   for(int j:g.neighbors[i])if(x[j]==dest)rate+=p[0]*p[2];
   for(int f:g.incident[i]){bool all=true;for(int k=0;k<g.q;++k){int j=g.face[g.q*f+k];if(j!=i && x[j]!=dest)all=false;}if(all)rate+=p[1]*p[2]*g.weight[f]*(1+(type==0?1.:-1.)*memory(f,t));}
   if(rate< -1e-8 || rate>g.bounds[z.channel]+1e-8)return -2.;accept=mark_uniform(seed,z.channel,z.count)*g.bounds[z.channel]<rate;
  }
  if(accept && x[i]!=dest){for(int f:g.incident[i]){a[f]=memory(f,t);last[f]=t;}nr+=(dest==1)-(x[i]==1);nc+=(dest==2)-(x[i]==2);x[i]=dest;for(int f:g.incident[i])phi[f]=drive(f);}
  uint64_t next=z.count+1;queue.push({t+exponential(seed,z.channel,next)/g.bounds[z.channel],z.channel,next});
 }
 while(obs<ng)record(grid[obs]);if(xe)for(int i=0;i<g.n;++i)xe[i]=x[i];if(ae)for(int f=0;f<g.f;++f)ae[f]=memory(f,end);return loss;
}
extern "C" int hyper_rollouts(int n,int m,int f,int q,const int* edges,const int* faces,const double* weights,const int* x,const double* a,const double* p,int nt,const int* targets,int reps,const uint64_t* seeds,int ng,const double* grid,double* trace,double* loss,int* xe,double* ae){
 HyperTopology g(n,m,f,q,edges,faces,weights,p);vector<int>chosen(targets,targets+nt);
 for(int r=0;r<reps;++r){loss[r]=hyper_path(g,x,a,p,chosen,seeds[r],ng,grid,trace+size_t(r)*ng*2,xe?xe+size_t(r)*n:nullptr,ae?ae+size_t(r)*f:nullptr);if(loss[r]<0)return 1;}return 0;
}
