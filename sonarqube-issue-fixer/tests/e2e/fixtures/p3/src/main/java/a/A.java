public class A {
  public int f(int[] a, int b, boolean c) {
    for (int x : a) {
      if (x > 0) {
        for (int y = 0; y < b; y++) {
          if (y > 1 && c || x > 2) {
            while (c) { if (b > 3) { try { b--; } catch (RuntimeException e) { if (b > 1) { continue; } } } }
          }
        }
      }
    }
    return 1;
  }
  public int g(int a,int b,int c,int d,int e,int f,int g,int h) { return a; }
}
