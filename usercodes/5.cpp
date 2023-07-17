// C++ program to implement iterative Binary Search
#include <bits/stdc++.h>
using namespace std;

int binarySearch(vector<int> &arr, int l, int r, int x){
    while (l <= r) {
        int m = l + (r - l) / 2;
        if (arr[m] == x)
            return m;

        if (arr[m] < x)
            l = m + 1;

        else
            r = m - 1;
    }

    return -1;
}

// Driver code
int main(void){
    int n;
    cin>>n;
    vector<int> arr(n);
    for(int i=0;i<n;i++){
        cin>>arr[i];
    }
    int x;
    cin>>x;
    int result = binarySearch(arr, 0, n - 1, x);
    cout<<result<<endl;
    return 0;
}