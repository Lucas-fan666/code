#include "../../vendor/src/graphical_engine.cpp"
#include <memory>
struct Handle {
 std::vector<int> edges,faces;
 std::vector<double> p;
 std::unique_ptr<GraphicalTopology> topology;
 Handle(int n,int m,int f,const int*e,const int*a,const double*q):
  edges(e,e+2*m),faces(a,a+3*f),p(q,q+7) {
  topology.reset(new GraphicalTopology(n,m,f,edges.data(),faces.data(),p.data()));
 }
};
extern "C" void* persistent_create(int n,int m,int f,const int*e,const int*a,const double*p){
 try{return new Handle(n,m,f,e,a,p);}catch(...){return nullptr;}
}
extern "C" void persistent_free(void*h){delete static_cast<Handle*>(h);}
extern "C" int persistent_stage(void*h,const int*x,const double*a,int M,const int*masks,
 const int*counts,int reps,const uint64_t*seeds,double*out){
 try{
  auto*g=static_cast<Handle*>(h);int n=g->topology->n;
  for(int j=0;j<M;j++){
   if(counts[j]<1||counts[j]>reps)return 2;
   std::vector<int>S;for(int i=0;i<n;i++)if(masks[j*n+i])S.push_back(i);
   for(int r=0;r<counts[j];r++){
    uint64_t di[2]={0,0};double v=graphical_one(*g->topology,x,a,g->p.data(),S,seeds[r],di);
    if(v<0)return 1;out[r*M+j]=v;
   }
  }return 0;
 }catch(...){return 3;}
}
