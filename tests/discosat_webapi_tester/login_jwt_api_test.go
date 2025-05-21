package discosat_webapi_tester

import (
	"errors"
	"strings"
	"testing"
)

const apiBaseURL = "http://127.0.0.1/"
const testAdminAccountName = "insecureAdminLogin"
const testAdminAccountPassword = "insecurePasswordRemoveAfterAdminCreated123onZhs2LipBPZVg2itHJsoS7U5tkywsxP"

func __createUserForTest(newUserName string, newUserPW string, newUserMail string, newUserRole string) error {
	SetupAPI(apiBaseURL)
	resp, _ := UserLogin(testAdminAccountName, testAdminAccountPassword)
	if resp.StatusCode() != 200 {
		return errors.New("Error while login testAdmin:" + resp.Status())
	}
	err := API_SetAccessTokenCookie(resp)
	if err != nil {
		return errors.New("Error handling JWT of testAdmin:" + err.Error())
	}
	resp, _ = Register(newUserName, newUserPW, newUserMail, newUserRole)
	if resp.StatusCode() != 200 {
		return errors.New("Error while create new test user:" + resp.Status())
	}
	resp, _ = Logout()
	if resp.StatusCode() != 200 {
		return errors.New("Error while logout testAdmin:" + resp.Status())
	}
	return nil
}

func __removeUserAfterTest(removeUserName string, removeUserMail string) error {
	SetupAPI(apiBaseURL) // reset the API
	resp, _ := UserLogin(testAdminAccountName, testAdminAccountPassword)
	if resp.StatusCode() != 200 {
		return errors.New("Error while login testAdmin:" + resp.Status())
	}
	err := API_SetAccessTokenCookie(resp)
	if err != nil {
		return errors.New("Error handling JWT of testAdmin:" + err.Error())
	}
	resp, _ = DeleteUser(removeUserName, removeUserMail)
	if resp.StatusCode() != 200 {
		return errors.New("Error while delete test user:" + resp.Status())
	}
	resp, _ = Logout()
	if resp.StatusCode() != 200 {
		return errors.New("Error while logout testAdmin:" + resp.Status())
	}
	return nil
}

func TestRequirements(t *testing.T) {
	SetupAPI(apiBaseURL)
	resp, _ := UserLogin(testAdminAccountName, testAdminAccountPassword)
	if resp.StatusCode() != 200 {
		t.Errorf("Unespected login-status: expected status 200, got status %d: %s", resp.StatusCode(), resp.String())
		return
	}
	err := API_SetAccessTokenCookie(resp)
	if err != nil {
		t.Errorf("no access-cookie found: %s", err.Error())
		return
	}
	resp, _ = Logout()
	if resp.StatusCode() != 200 {
		t.Errorf("Unespected logout-status: expected status 200, got status %d: %s", resp.StatusCode(), resp.String())
		return
	}
}

func TestUserLogin_wrongUser(t *testing.T) {
	// prepare
	unknownUser := "user_TestLogin_unknownUserName"
	SetupAPI(apiBaseURL)
	// test the method
	resp, err := UserLogin(unknownUser, "test_foo")
	if err != nil {
		if resp.StatusCode() != 403 {
			t.Errorf("Expected Error-Status 403, but got %d", resp.StatusCode())
		}
	} else {
		t.Errorf("Unexpected run of test UserLogin.wrongUserName without the expected error.")
	}
	// cleanup
}

func TestUserLogin_wrongPassword(t *testing.T) {
	// prepare
	newUser := "user_TestLogin_wrongPassword"
	newPassword := "password_TestLogin_wrongPassword"
	newEmail := "testmail@test.com"
	err := __createUserForTest(newUser, newPassword, newEmail, "user")
	if err != nil {
		t.Errorf("Error during test-preparation: %s", err.Error())
	}
	SetupAPI(apiBaseURL) // reset the API
	// test the method
	resp, err := UserLogin(newUser, newPassword+"thisIsWrong")
	if err != nil {
		if resp.StatusCode() != 403 {
			t.Errorf("Expected Error-Status 403, but got %d", resp.StatusCode())
		}
	} else {
		t.Errorf("Unexpected run of test UserLogin.wrongUserName without the expected error.")
	}
	// cleanup
	err = __removeUserAfterTest(newUser, newEmail)
	if err != nil {
		t.Errorf("Error during test-cleanup: %s", err.Error())
	}
}

func TestUserLogin_correct(t *testing.T) {
	// prepare
	newUser := "user_TestLogin_correct"
	newPassword := "password_TestLogin_correct"
	newEmail := "testmail@test.com"
	err := __createUserForTest(newUser, newPassword, newEmail, "user")
	if err != nil {
		t.Errorf("Error during test-preparation: %s", err.Error())
	}
	SetupAPI(apiBaseURL) // reset the API
	// perform the test
	resp, _ := UserLogin(newUser, newPassword)
	if resp.StatusCode() != 200 {
		t.Errorf("Expected Error-Status 200, but got %d: %s", resp.StatusCode(), resp.String())
	}
	// cleanup
	err = __removeUserAfterTest(newUser, newEmail)
	if err != nil {
		t.Errorf("Error during test-cleanup: %s", err.Error())
	}
}

func TestUserLogin_multiLogins(t *testing.T) {
	// prepare
	newUser := "user_TestLogin_multiLogins"
	newPassword := "password_TestLogin_multiLogins"
	newEmail := "testmail@test.com"
	err := __createUserForTest(newUser, newPassword, newEmail, "user")
	if err != nil {
		t.Errorf("Error during test-preparation: %s", err.Error())
	}
	SetupAPI(apiBaseURL) // reset the API
	// perform the test
	resp1, _ := UserLogin(newUser, newPassword)
	if resp1.StatusCode() != 200 {
		t.Errorf("Expected Error-Status 200, but got %d: %s", resp1.StatusCode(), resp1.String())
	}
	resp2, _ := UserLogin(newUser, newPassword)
	if resp2.StatusCode() != 200 {
		t.Errorf("Expected Error-Status 200, but got %d: %s", resp2.StatusCode(), resp2.String())
	}
	SetupAPI(apiBaseURL) // reset the API
	err = API_SetAccessTokenCookie(resp1)
	if err != nil {
		t.Errorf("Error setting access-cookie: %s", err.Error())
	}
	resp3, _ := Logout()
	if resp3.StatusCode() != 401 || strings.Contains(resp3.Status(), "Invalid token") {
		t.Errorf("Expected Error-Status 401, but got %d: %s", resp3.StatusCode(), resp3.String())
	}
	SetupAPI(apiBaseURL) // reset the API
	err = API_SetAccessTokenCookie(resp2)
	if err != nil {
		t.Errorf("Error setting access-cookie: %s", err.Error())
	}
	resp4, _ := Logout()
	if resp4.StatusCode() != 200 {
		t.Errorf("Expected Error-Status 200, but got %d: %s", resp4.StatusCode(), resp4.String())
	}
	// cleanup
	err = __removeUserAfterTest(newUser, newEmail)
	if err != nil {
		t.Errorf("Error during test-cleanup: %s", err.Error())
	}
}

func TestRegister_noLogin(t *testing.T) {
	//prepare
	newUser := "user_TestRegister_noLogin"
	newPassword := "password_TestRegister_noLogin"
	newEmail := "testmail@test.com"
	SetupAPI(apiBaseURL) // reset the API
	// perform the test
	resp, _ := Register(newUser, newPassword, newEmail, "user")
	if resp.StatusCode() != 401 {
		t.Errorf("Expected Error-Status 401, but got %d: %s", resp.StatusCode(), resp.String())
	}
	// cleanup
}

func TestRegister_wrongRights(t *testing.T) {
	//prepare
	newUser := "user_TestRegister_wrongRights"
	newPassword := "password_TestRegister_wrongRights"
	newEmail := "testmail@test.com"
	err := __createUserForTest(newUser, newPassword, newEmail, "user")
	if err != nil {
		t.Errorf("Error during test-preparation: %s", err.Error())
	}
	SetupAPI(apiBaseURL) // reset the API
	// perform the test
	resp, _ := UserLogin(newUser, newPassword)
	_ = API_SetAccessTokenCookie(resp)
	resp, _ = Register("anotherTestUser", "anotherTestPassword", "anotherMail@test.com", "user")
	if resp.StatusCode() != 403 {
		t.Errorf("Expected Error-Status 403, but got %d: %s", resp.StatusCode(), resp.String())
	}
	// cleanup
	err = __removeUserAfterTest(newUser, newEmail)
	if err != nil {
		t.Errorf("Error during test-cleanup: %s", err.Error())
	}
}

func TestRegister_wrongType(t *testing.T) {
	//prepare
	newUser := "user_TestRegister_wrongType"
	newPassword := "password_TestRegister_wongType"
	newEmail := "testmail@test.com"
	err := __createUserForTest(newUser, newPassword, newEmail, "user")
	if err != nil {
		t.Errorf("Error during test-preparation: %s", err.Error())
	}
	SetupAPI(apiBaseURL) // reset the API
	// perform the test
	resp, _ := UserLogin(newUser, newPassword)
	_ = API_SetAccessTokenCookie(resp)
	resp, _ = Register("anotherTestUser", "anotherTestPassword", "anotherMail@test.com", "user")
	if resp.StatusCode() != 403 {
		t.Errorf("Expected Error-Status 403, but got %d: %s", resp.StatusCode(), resp.String())
	}
	// cleanup
	err = __removeUserAfterTest(newUser, newEmail)
	if err != nil {
		t.Errorf("Error during test-cleanup: %s", err.Error())
	}
}

func TestRegister_existingUser(t *testing.T) {
	//prepare
	newUser := "user_TestRegister_existingUser"
	newPassword := "password_TestRegister_existingUser"
	newEmail := "testmail@test.com"
	err := __createUserForTest(newUser, newPassword, newEmail, "admin")
	if err != nil {
		t.Errorf("Error during test-preparation: %s", err.Error())
	}
	SetupAPI(apiBaseURL) // reset the API
	// perform the test
	resp, _ := UserLogin(newUser, newPassword)
	_ = API_SetAccessTokenCookie(resp)
	resp, _ = Register(newUser, newPassword, newEmail, "user")
	if resp.StatusCode() != 500 || strings.Contains(resp.Status(), "Username already used") {
		t.Errorf("Expected Error-Status 200, but got %d: %s", resp.StatusCode(), resp.String())
	}
	// cleanup
	err = __removeUserAfterTest(newUser, newEmail)
	if err != nil {
		t.Errorf("Error during test-cleanup: %s", err.Error())
	}
}

func TestRegister_works(t *testing.T) {
	//prepare
	newUser := "user_TestRegister_works"
	newPassword := "password_TestRegister_works"
	newEmail := "testmail@test.com"
	err := __createUserForTest(newUser, newPassword, newEmail, "admin")
	if err != nil {
		t.Errorf("Error during test-preparation: %s", err.Error())
	}
	SetupAPI(apiBaseURL) // reset the API
	// perform the test
	resp, _ := UserLogin(newUser, newPassword)
	newUser2 := "user2_TestRegister_works"
	newPassword2 := "password2_TestRegister_works"
	newEmail2 := "anotherMail@test.com"
	_ = API_SetAccessTokenCookie(resp)
	resp, _ = Register(newUser2, newPassword2, newEmail2, "user")
	if resp.StatusCode() != 200 {
		t.Errorf("Expected Error-Status 200, but got %d: %s", resp.StatusCode(), resp.String())
	}
	// cleanup
	err = __removeUserAfterTest(newUser, newEmail)
	err = __removeUserAfterTest(newUser2, newEmail2)
	if err != nil {
		t.Errorf("Error during test-cleanup: %s", err.Error())
	}
}

func TestRefresh_notLogin(t *testing.T) {
	//prepare
	SetupAPI(apiBaseURL) // reset the API
	// perform the test
	API_Wrong_SetAccessTokenCookie()
	API_Wrong_SetRefreshTokenCookie()
	resp, _ := Refresh()
	if resp.StatusCode() != 401 {
		t.Errorf("Expected Error-Status 401, but got %d: %s", resp.StatusCode(), resp.String())
	}
	// cleanup
}

func TestRefresh_onlyAcc(t *testing.T) {
	//prepare
	SetupAPI(apiBaseURL) // reset the API
	resp, _ := UserLogin(testAdminAccountName, testAdminAccountPassword)
	// perform the test
	SetupAPI(apiBaseURL) // reset the API to remove all cookies in the background
	_ = API_SetAccessTokenCookie(resp)
	resp, _ = Refresh()
	if resp.StatusCode() != 401 {
		t.Errorf("Expected Error-Status 401, but got %d: %s", resp.StatusCode(), resp.String())
	}
	// cleanup
	resp, _ = Logout()
	if resp.StatusCode() != 200 {
		t.Errorf("Error while cleanup logout testAdmin: %s", resp.Status())
	}
}

func TestRefresh_onlyRefresh(t *testing.T) {
	//prepare
	SetupAPI(apiBaseURL) // reset the API
	resp, _ := UserLogin(testAdminAccountName, testAdminAccountPassword)
	// perform the test
	SetupAPI(apiBaseURL) // reset the API to remove all cookies in the background
	err := API_SetRefreshTokenCookie(resp)
	if err != nil {
		t.Errorf("Error setting refresh-cookie: %s", err.Error())
	}
	resp2, _ := Refresh()
	if resp2.StatusCode() != 200 {
		t.Errorf("Expected Error-Status 200, but got %d: %s", resp2.StatusCode(), resp2.String())
	}
	// cleanup
	resp3, _ := Logout()
	if resp3.StatusCode() != 200 {
		t.Errorf("Error while logout testAdmin:" + resp3.Status())
	}
}

func TestRefresh_bothTokens(t *testing.T) {
	//prepare
	SetupAPI(apiBaseURL) // reset the API
	resp, _ := UserLogin(testAdminAccountName, testAdminAccountPassword)
	// perform the test
	SetupAPI(apiBaseURL) // reset the API to remove all cookies in the background
	err := API_SetAccessTokenCookie(resp)
	if err != nil {
		t.Errorf("Error setting access-cookie: %s", err.Error())
	}
	err = API_SetRefreshTokenCookie(resp)
	if err != nil {
		t.Errorf("Error setting refresh-cookie: %s", err.Error())
	}
	resp2, _ := Refresh()
	if resp2.StatusCode() != 200 {
		t.Errorf("Expected Error-Status 200, but got %d: %s", resp2.StatusCode(), resp2.String())
	}
	// cleanup
	resp3, _ := Logout()
	if resp3.StatusCode() != 200 {
		t.Errorf("Error while logout testAdmin:" + resp3.Status())
	}
}

func TestRefresh_oldInvalid1(t *testing.T) {
	//prepare
	SetupAPI(apiBaseURL) // reset the API
	resp1, _ := UserLogin(testAdminAccountName, testAdminAccountPassword)
	resp2, _ := UserLogin(testAdminAccountName, testAdminAccountPassword)
	// perform the test
	SetupAPI(apiBaseURL) // reset the API to remove all cookies in the background
	err := API_SetRefreshTokenCookie(resp1)
	if err != nil {
		t.Errorf("Error setting refresh-cookie: %s", err.Error())
	}
	resp3, _ := Refresh()
	if resp3.StatusCode() != 401 {
		t.Errorf("Expected Error-Status 401, but got %d: %s", resp3.StatusCode(), resp3.String())
	}
	// cleanup
	SetupAPI(apiBaseURL) // reset the API to remove all cookies in the background
	_ = API_SetAccessTokenCookie(resp2)
	resp4, _ := Logout()
	if resp4.StatusCode() != 200 {
		t.Errorf("Error while logout testAdmin:" + resp4.Status())
	}
}

func TestRefresh_oldInvalid2(t *testing.T) {
	//prepare
	SetupAPI(apiBaseURL) // reset the API
	resp1, _ := UserLogin(testAdminAccountName, testAdminAccountPassword)
	_ = API_SetRefreshTokenCookie(resp1)
	resp2, _ := Refresh()
	if resp2.StatusCode() != 200 {
		t.Errorf("Error during prepare: Refresh got status %d: %s", resp2.StatusCode(), resp2.String())
	}
	// perform the test
	SetupAPI(apiBaseURL) // reset the API to remove all cookies in the background
	err := API_SetRefreshTokenCookie(resp1)
	if err != nil {
		t.Errorf("Error setting refresh-cookie: %s", err.Error())
	}
	resp3, _ := Refresh()
	if resp3.StatusCode() != 401 {
		t.Errorf("Expected Error-Status 401, but got %d: %s", resp3.StatusCode(), resp3.String())
	}
	// cleanup
	SetupAPI(apiBaseURL) // reset the API to remove all cookies in the background
	_ = API_SetAccessTokenCookie(resp2)
	resp4, _ := Logout()
	if resp4.StatusCode() != 200 {
		t.Errorf("Error while logout testAdmin:" + resp4.Status())
	}
}

func TestLogout_notLogin(t *testing.T) {
	//prepare
	SetupAPI(apiBaseURL) // reset the API
	resp1, _ := UserLogin(testAdminAccountName, testAdminAccountPassword)
	resp2, _ := Logout()
	if resp2.StatusCode() != 200 {
		t.Errorf("Error while logout testAdmin:" + resp2.Status())
	}
	// perform the test
	SetupAPI(apiBaseURL) // reset the API to remove all cookies in the background
	err := API_SetAccessTokenCookie(resp1)
	if err != nil {
		t.Errorf("Error setting access-cookie: %s", err.Error())
	}
	resp3, _ := Logout()
	if resp3.StatusCode() != 401 {
		t.Errorf("Expected Error-Status 401, but got %d: %s", resp3.StatusCode(), resp3.String())
	}
	// cleanup
}

func TestLogout_works(t *testing.T) {
	//prepare
	SetupAPI(apiBaseURL) // reset the API
	resp1, _ := UserLogin(testAdminAccountName, testAdminAccountPassword)
	// perform the test
	SetupAPI(apiBaseURL) // reset the API to remove all cookies in the background
	err := API_SetAccessTokenCookie(resp1)
	if err != nil {
		t.Errorf("Error setting access-cookie: %s", err.Error())
	}
	resp2, _ := Logout()
	if resp2.StatusCode() != 200 {
		t.Errorf("Expected Error-Status 200, but got %d: %s", resp2.StatusCode(), resp2.String())
	}
	// cleanup
}

func TestDeleteUser_noAdmin(t *testing.T) {
	//prepare
	newUser := "user_TestDeleteUser_noAdmin"
	newPassword := "password_TestDeleteUser_noAdmin"
	newEmail := "testmail@test.com"
	err := __createUserForTest(newUser, newPassword, newEmail, "user")
	if err != nil {
		t.Errorf("Error during test-preparation: %s", err.Error())
	}
	SetupAPI(apiBaseURL) // reset the API
	// perform the test
	resp, _ := UserLogin(newUser, newPassword)
	_ = API_SetAccessTokenCookie(resp)
	resp, _ = DeleteUser(newUser, newEmail)
	if resp.StatusCode() != 403 {
		t.Errorf("Expected Error-Status 403, but got %d: %s", resp.StatusCode(), resp.String())
	}
	// cleanup
	err = __removeUserAfterTest(newUser, newEmail)
	if err != nil {
		t.Errorf("Error during test-cleanup: %s", err.Error())
	}
}

func TestDeleteUser_notExisting(t *testing.T) {
	//prepare
	newUser := "user_TestDeleteUser_notExisting"
	newEmail := "testmail@test.com"
	SetupAPI(apiBaseURL) // reset the API
	// perform the test
	resp, _ := UserLogin(testAdminAccountName, testAdminAccountPassword)
	_ = API_SetAccessTokenCookie(resp)
	resp, _ = DeleteUser(newUser, newEmail)
	if resp.StatusCode() != 500 || strings.Contains(resp.Status(), "Could not delete user") {
		t.Errorf("Expected Error-Status 500, but got %d: %s", resp.StatusCode(), resp.String())
	}
	// cleanup
	resp3, _ := Logout()
	if resp3.StatusCode() != 200 {
		t.Errorf("Error in cleanup: logout testAdmin:" + resp3.Status())
	}
}

func TestDeleteUser_works(t *testing.T) {
	//prepare
	newUser := "user_TestDeleteUser_noAdmin"
	newPassword := "password_TestDeleteUser_noAdmin"
	newEmail := "testmail@test.com"
	err := __createUserForTest(newUser, newPassword, newEmail, "user")
	if err != nil {
		t.Errorf("Error during test-preparation: %s", err.Error())
	}
	SetupAPI(apiBaseURL) // reset the API
	// perform the test
	resp, _ := UserLogin(testAdminAccountName, testAdminAccountPassword)
	_ = API_SetAccessTokenCookie(resp)
	resp, _ = DeleteUser(newUser, newEmail)
	if resp.StatusCode() != 200 {
		t.Errorf("Expected Status 200, but got %d: %s", resp.StatusCode(), resp.String())
	}
	resp, _ = UserLogin(newUser, newPassword)
	if resp.StatusCode() != 403 || strings.Contains(resp.Status(), "Invalid Login") {
		t.Errorf("Expected Error-Status 403, but got %d: %s", resp.StatusCode(), resp.String())
	}
	// cleanup
}

func TestLogout_WithHeader(t *testing.T) {
	//prepare
	newSensor := "sensor_TestLogout_WithHeader"
	newPassword := "password_TestLogout_WithHeader"
	newEmail := "testmail@test.com"
	err := __createUserForTest(newSensor, newPassword, newEmail, "sensor")
	if err != nil {
		t.Errorf("Error during test-preparation: %s", err.Error())
	}
	// perform the test
	SetupAPI(apiBaseURL) // reset the API to remove all cookies in the background
	resp, _ := UserLogin(newSensor, newPassword)
	SetupAPI(apiBaseURL)
	err = API_SetAccessTokenHeader_fromRespCookie(resp)
	if err != nil {
		t.Errorf("Error setting access-token header: %s", err.Error())
	}
	resp, err = Logout()
	if resp.StatusCode() != 200 {
		t.Errorf("Expected Status 200, but got %d: %s", resp.StatusCode(), resp.String())
	}
	// cleanup
	err = __removeUserAfterTest(newSensor, newEmail)
	if err != nil {
		t.Errorf("Error during test-cleanup: %s", err.Error())
	}
}

func TestRefreshSensor_WithHeader(t *testing.T) {
	//prepare
	newSensor := "sensor_TestRefresh_WithHeader"
	newPassword := "password_TestRefresh_WithHeader"
	newEmail := "testmail@test.com"
	err := __createUserForTest(newSensor, newPassword, newEmail, "sensor")
	if err != nil {
		t.Errorf("Error during test-preparation: %s", err.Error())
	}
	// perform the test
	SetupAPI(apiBaseURL) // reset the API to remove all cookies in the background
	resp, _ := UserLogin(newSensor, newPassword)
	SetupAPI(apiBaseURL)
	err = API_SetRefreshTokenHeader_fromRespCookie(resp)
	if err != nil {
		t.Errorf("Error setting refresh-token header: %s", err.Error())
	}
	resp, myTokenReply, _ := RefreshSensor()
	if resp.StatusCode() != 200 {
		t.Errorf("Expected Status 200, but got %d: %s", resp.StatusCode(), resp.String())
	}
	SetupAPI(apiBaseURL)
	err = API_SetAccessTokenHeader_fromRespBody(myTokenReply)
	if err != nil {
		t.Errorf("Error setting access-token header: %s", err.Error())
	}
	resp, err = Logout()
	if resp.StatusCode() != 200 {
		t.Errorf("Expected Status 200, but got %d: %s", resp.StatusCode(), resp.String())
	}
	// cleanup
	err = __removeUserAfterTest(newSensor, newEmail)
	if err != nil {
		t.Errorf("Error during test-cleanup: %s", err.Error())
	}
}
