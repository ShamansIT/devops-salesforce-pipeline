@IsTest
private class DevopsDemoTest {
    @IsTest
    static void testAdd() {
        Integer result = DevopsDemo.add(2, 3);
        System.assertEquals(5, result);
    }
}
