#include "../vendor/src/graphical_engine.cpp"

// Instrumented copy of the archived exact reset-tape simulator.  It continues
// after rumor extinction because memory and correction curves are requested.
static double trace_one(const GraphicalTopology& g, const int* x0,
 const double* a0, const double* p, const vector<int>& targets, uint64_t seed,
 int ng, const double* grid, double* out) {
 vector<int> x(x0,x0+g.n); vector<char> target(g.n,0);
 for(int i:targets) target[i]=1;
 vector<double> a(a0,a0+g.f), last(g.f,0.), phi(g.f);
 auto drive=[&](int f){int r=0,c=0;for(int k=0;k<3;++k){
  int z=x[g.faces[3*f+k]];r+=z==1;c+=z==2;}
  return p[2]*((r>=2)-(c>=2));};
 for(int f=0;f<g.f;++f)phi[f]=drive(f);
 auto memory=[&](int f,double t){return phi[f]+(a[f]-phi[f])*std::exp(-p[3]*(t-last[f]));};
 int obs=0; auto record=[&](double t){
  int nr=0,nc=0;for(int z:x){nr+=z==1;nc+=z==2;}
  double ma=0;for(int f=0;f<g.f;++f)ma+=memory(f,t);
  out[4*obs]=double(nr)/g.n;out[4*obs+1]=double(nc)/g.n;
  out[4*obs+2]=double(g.n-nr-nc)/g.n;
  out[4*obs+3]=g.f?ma/g.f:0.;++obs;
 };
 std::priority_queue<Proposal,vector<Proposal>,Later> queue;
 for(int k=0;k<3*g.n;++k)if(g.bounds[k]>0)
  queue.push({exponential(seed,k,0)/g.bounds[k],k,0});
 double t=0.,loss=0.,D=p[5],end=D+p[6];int nr=0;for(int z:x)nr+=z==1;
 uint64_t steps=0;
 while(!queue.empty()){
  Proposal q=queue.top();queue.pop();double until=std::min(end,q.time);
  while(obs<ng && grid[obs]<=until)record(grid[obs]);
  loss+=double(nr)/g.n*std::max(0.,until-std::max(t,D));t=until;
  if(q.time>=end)break;
  if(++steps>50000000)return -1.;
  int i=q.channel/3,type=q.channel%3,dest=(type==0?1:(type==1?2:0));
  bool accepted=type==2;
  if(type!=2 && x[i]!=dest){
   double rate=(type==1 && target[i] && t<D?p[4]:0.);
   for(int j:g.neighbors[i])if(x[j]==dest)rate+=p[0]*p[2];
   for(int f:g.incident[i]){
    bool both=true;for(int k=0;k<3;++k){int v=g.faces[3*f+k];if(v!=i && x[v]!=dest)both=false;}
    if(both)rate+=p[1]*p[2]*(1+(type==0?1.:-1.)*memory(f,t));
   }
   if(rate>g.bounds[q.channel]+1e-8 || rate< -1e-8)return -1.;
   accepted=mark_uniform(seed,q.channel,q.count)*g.bounds[q.channel]<rate;
  }
  if(accepted && x[i]!=dest){
   for(int f:g.incident[i]){a[f]=memory(f,t);last[f]=t;}
   nr+=(dest==1)-(x[i]==1);x[i]=dest;
   for(int f:g.incident[i])phi[f]=drive(f);
  }
  uint64_t next=q.count+1;
  queue.push({t+exponential(seed,q.channel,next)/g.bounds[q.channel],q.channel,next});
 }
 while(obs<ng)record(grid[obs]);
 return loss;
}

extern "C" int traced_rollouts(int n,int m,int f,const int* e,const int* faces,
 const int* x,const double* a,const double* p,int nt,const int* targets,
 int reps,const uint64_t* seeds,int ng,const double* grid,double* traces,double* losses){
 GraphicalTopology graph(n,m,f,e,faces,p);vector<int> chosen(targets,targets+nt);
 for(int r=0;r<reps;++r){
  losses[r]=trace_one(graph,x,a,p,chosen,seeds[r],ng,grid,traces+size_t(r)*ng*4);
  if(losses[r]<0)return 1;
 }return 0;
}
