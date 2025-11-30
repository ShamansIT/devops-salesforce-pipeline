public with sharing class DevopsDemo {
    public static Integer add(Integer a, Integer b) {
        if (a == null) a = 0;
        if (b == null) b = 0;
        return a + b;
    }
}