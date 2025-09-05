// SleepMain.java
public class SleepMain {
  public static void main(String[] args) throws Exception {
    System.out.println("SleepMain PID=" + ProcessHandle.current().pid());
    Thread.sleep(600_000); // 10 minutes
  }
}
