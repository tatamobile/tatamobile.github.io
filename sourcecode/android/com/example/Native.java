package com.example;

public class Native{
    public static native int GetSample();
    public static native int GetSample(int n, String s,int [] arr);
    public static class Stub{
        public static native int GetSample();
    }
}

