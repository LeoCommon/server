package discosat_webapi_tester

import (
	"testing"
)

func TestGetJobs_works(t *testing.T) {
	//prepare
	newSensor := "sensor_TestGetJobs_works"
	newPassword := "password_TestGetJobs_works"
	newMail := "testmail@test.com"
	newRole := "sensor"
	err := __createUserForTest(newSensor, newPassword, newMail, newRole)
	if err != nil {
		t.Errorf("Error during test-preparation: %s", err.Error())
	}
	// perform the test
	SetupAPI(apiBaseURL) // reset the API
	resp, _ := UserLogin(newSensor, newPassword)
	_ = API_SetAccessTokenCookie(resp)
	resp, _, err = GetJobs(newSensor)
	if resp.StatusCode() != 200 {
		t.Errorf("Expected Status 200, but got %d: %s", resp.StatusCode(), resp.String())
	}
	resp, _ = Logout()
	if resp.StatusCode() != 200 {
		t.Errorf("Error while logout testSensor:" + resp.Status())
	}
	// cleanup
	err = __removeUserAfterTest(newSensor, newMail)
	if err != nil {
		t.Errorf("Error during test-cleanup: %s", err.Error())
	}
}
