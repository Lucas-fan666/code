#include "engine/engine.cpp"
// The path kernel is unchanged. Only topology construction is shared across
// replications having different initial states; no random input is shared
// between independent replications.
extern "C" int varied_rollouts(int n,int m,int f,int q,const int* edges,
 const int* faces,const double* weights,const int* x,const double* a,
 const double* p,int nt,const int* targets,int reps,const uint64_t* seeds,
 int ng,const double* grid,double* trace,double* loss,int* xe,double* ae){
 HyperTopology g(n,m,f,q,edges,faces,weights,p);
 vector<int> chosen(targets,targets+nt);
 for(int r=0;r<reps;++r){
  loss[r]=hyper_path(g,x+size_t(r)*n,a+size_t(r)*f,p,chosen,seeds[r],ng,grid,
    trace+size_t(r)*ng*2,xe+size_t(r)*n,ae+size_t(r)*f);
  if(loss[r]<0)return 1;
 }
 return 0;
}
