#include <bits/stdc++.h>
using namespace std;

int main(){
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int t; cin>>t;
    while(t--){
        int n; cin>>n;
        if(n<=2){
            cout<<string(n,'1')<<'\n';
            continue;
        }

        int m=n+1,c[3]={m/3,(m+1)/3,(m+2)/3},e=-1;
        string str_1(n,'0');

        for(int i=0;i<3;i++){
            if(c[i]%2==0){
                e=i;
                break;
            }
        }

        if(e!=-1){
            swap(c[1],c[e]);
            int a=c[0],b=c[1];
            str_1[a-1]=str_1[a+b-1]='1';
        }else{
            int q=m/3;
            str_1[q-1]=str_1[2*q-2]=str_1[n-1]='1';
        }

        cout<<str_1<<'\n';
    }
}
