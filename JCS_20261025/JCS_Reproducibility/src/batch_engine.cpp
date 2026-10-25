// Multi-copy destination-reset coupling. General principle: stacked coupling.
// Local adaptive envelopes specialize it to exponentially relaxing face memory.
#include "../vendor/src/graphical_engine.cpp"
#include <random>
#include <stdexcept>
struct Fenwick {
 int n; vector<double> tree,values; Fenwick(int N):n(N),tree(N+1,0),values(N,0){}
 void set(int i,double v){double d=v-values[i];values[i]=v;for(int j=i+1;j<=n;j+=j&-j)tree[j]+=d;}
 double total()const{double s=0;for(int j=n;j>0;j-=j&-j)s+=tree[j];return s;}
 int pick(double v)const{int i=0;double s=0;int b=1;while((b<<1)<=n)b<<=1;for(;b;b>>=1){int j=i+b;if(j<=n&&s+tree[j]<=v){i=j;s+=tree[j];}}return std::min(i,n-1);}
};
struct Copy {
 vector<int>x;vector<unsigned char>target;vector<double>a,last,phi;int rumor=0;double loss=0;
 Copy(const GraphicalTopology&g,const int*x0,const double*a0,const double*p,const int*mask):x(x0,x0+g.n),target(g.n),a(a0,a0+g.f),last(g.f,0),phi(g.f){
  for(int i=0;i<g.n;i++){target[i]=mask[i];rumor+=x[i]==1;}for(int f=0;f<g.f;f++)phi[f]=drive(g,f,p);
 }
 double drive(const GraphicalTopology&g,int f,const double*p)const{int r=0,c=0;for(int j=0;j<3;j++){int v=x[g.faces[3*f+j]];r+=v==1;c+=v==2;}return p[2]*((r>=2)-(c>=2));}
 double memory(int f,double t,const double*p)const{return phi[f]+(a[f]-phi[f])*std::exp(-p[3]*(t-last[f]));}
 double rate(const GraphicalTopology&g,int i,int type,double t,const double*p,bool bound)const{
  int dest=type==0?1:type==1?2:0;if(x[i]==dest)return 0;if(type==2)return 1;
  double r=type==1&&target[i]&&t<p[5]?p[4]:0;
  for(int j:g.neighbors[i])if(x[j]==dest)r+=p[0]*p[2];
  for(int f:g.incident[i]){bool both=true;for(int j=0;j<3;j++){int v=g.faces[3*f+j];if(v!=i&&x[v]!=dest)both=false;}
   if(both){double mem=memory(f,t,p);if(bound&&p[3]>0)mem=type==0?std::max(mem,phi[f]):std::min(mem,phi[f]);r+=p[1]*p[2]*(1+(type==0?1:-1)*mem);}}
  return r;
 }
 void jump(const GraphicalTopology&g,int i,int dest,double t,const double*p){for(int f:g.incident[i]){a[f]=memory(f,t,p);last[f]=t;}rumor+=(dest==1)-(x[i]==1);x[i]=dest;for(int f:g.incident[i])phi[f]=drive(g,f,p);}
};
// mode 0: fixed proposal tape, exactly replay-compatible with old engine.
// mode 1: adaptive local refresh; mode 2: adaptive global refresh reference.
extern "C" int batch_rollouts(int n,int m,int f,const int*e,const int*faces,const int*x0,const double*a0,const double*p,int copies,const int*masks,int reps,const uint64_t*seeds,int mode,double*out,uint64_t*di){
 try{GraphicalTopology g(n,m,f,e,faces,p);
 for(int r=0;r<reps;r++){
  vector<Copy> z;z.reserve(copies);for(int j=0;j<copies;j++)z.emplace_back(g,x0,a0,p,masks+j*n);
  double t=0,end=p[5]+p[6];uint64_t proposed=0,jumps=0,refreshes=0;
  auto integrate=[&](double s){double dt=std::max(0.,s-std::max(t,p[5]));for(auto&c:z)c.loss+=double(c.rumor)/n*dt;t=s;};
  if(mode==0){
   std::priority_queue<Proposal,vector<Proposal>,Later>q;for(int c=0;c<3*n;c++)if(g.bounds[c]>0)q.push({exponential(seeds[r],c,0)/g.bounds[c],c,0});
   while(!q.empty()){
    bool alive=false;for(auto&c:z)alive|=c.rumor>0;if(!alive)break;
    auto v=q.top();q.pop();integrate(std::min(end,v.time));if(v.time>=end)break;
    if(++proposed>50000000)return 2;int i=v.channel/3,type=v.channel%3,dest=type==0?1:type==1?2:0;
    double mark=mark_uniform(seeds[r],v.channel,v.count)*g.bounds[v.channel];
    for(auto&c:z)if(c.rumor>0&&c.x[i]!=dest){double rate=c.rate(g,i,type,t,p,false);if(rate>g.bounds[v.channel]+1e-8)return 3;if(type==2||mark<rate){c.jump(g,i,dest,t,p);jumps++;}}
    uint64_t next=v.count+1;q.push({t+exponential(seeds[r],v.channel,next)/g.bounds[v.channel],v.channel,next});
   }
  }else{
   Fenwick b(3*n);std::mt19937_64 rng(seeds[r]);auto unif=[&](){return (double(rng()>>11)+.5)*0x1.0p-53;};
   auto refresh=[&](int i){for(int type=0;type<3;type++){double hi=0;for(auto&c:z)hi=std::max(hi,c.rate(g,i,type,t,p,true));b.set(3*i+type,hi);}refreshes++;};
   for(int i=0;i<n;i++)refresh(i);
   vector<int>stamp(n,0);int epoch=0;
   while(t<end){double sum=b.total();double s=sum>1e-12?t-std::log(unif())/sum:end;
    if(t<p[5]&&s>=p[5]){integrate(p[5]);for(int i=0;i<n;i++)refresh(i);continue;}
    integrate(std::min(end,s));if(s>=end)break;
    if(++proposed>50000000)return 2;int channel=b.pick(unif()*sum),i=channel/3,type=channel%3,dest=type==0?1:type==1?2:0;
    double mark=unif()*b.values[channel];bool changed=false;
    for(auto&c:z){double rate=c.rate(g,i,type,t,p,false);if(rate>b.values[channel]+1e-8||rate< -1e-8)return 3;if(mark<rate){c.jump(g,i,dest,t,p);jumps++;changed=true;}}
    if(changed){if(mode==2){for(int j=0;j<n;j++)refresh(j);}else{
      epoch++;auto touch=[&](int j){if(stamp[j]!=epoch){stamp[j]=epoch;refresh(j);}};
      touch(i);for(int j:g.neighbors[i])touch(j);for(int face:g.incident[i])for(int k=0;k<3;k++)touch(g.faces[3*face+k]);
    }}
   }
  }
  for(int j=0;j<copies;j++)out[r*copies+j]=z[j].loss;
  di[3*r]=proposed;di[3*r+1]=jumps;di[3*r+2]=refreshes;
 }
 return 0;}catch(...){return 9;}
}
