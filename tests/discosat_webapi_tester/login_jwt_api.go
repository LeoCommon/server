package discosat_webapi_tester

import (
	"errors"
	"log"
	"net/http"
	"time"

	"github.com/go-resty/resty/v2"
)

// Some structs to handle the Json, coming from the server

type LoginRequestBody struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

type RegisterRequestBody struct {
	Email    string `json:"email"`
	Username string `json:"username"`
	Password string `json:"password"`
	Role     string `json:"role"`
}

type SensorTokenRequestBody struct {
	SensorName string `json:"sensor_name"`
}

type DeleteUserRequestBody struct {
	Email    string `json:"email"`
	Username string `json:"username"`
	Password string `json:"password"`
	Role     string `json:"role"`
}

type DeleteBasicAuthRequestBody struct {
	SensorName string `json:"sensorname"`
}

type TokenReply struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
}

// Local variables to handle the connection
var client *resty.Client

// Constants of the rest-client
const ClientTimeout = 10 * time.Second
const ClientRetryWaitTime = 10 * time.Second

func SetupAPI(baseURL string) {

	//set up the connection
	client = resty.New()
	// Set up the api base-url
	client.SetBaseURL(baseURL)

	//client.SetBasicAuth(sensorName, sensorPw)
	// Some connection configurations
	client.SetTimeout(ClientTimeout)
	client.SetRetryCount(3)
	client.SetRetryWaitTime(ClientRetryWaitTime)
	client.SetRetryMaxWaitTime(ClientRetryWaitTime)
}

func UserLogin(userName string, userPassword string) (*resty.Response, error) {
	loginBody := LoginRequestBody{}
	loginBody.Username = userName
	loginBody.Password = userPassword

	resp, err := client.R().
		SetHeader("Content-Type", "application/json").
		SetBody(loginBody).
		Post("login/userlogin")
	if err != nil {
		log.Print(err.Error())
		return resp, err
	}
	if resp.StatusCode() == 403 {
		return resp, errors.New("UserLogin: status 403 " + resp.String())
	} else if resp.StatusCode() != 200 {
		return resp, errors.New("UserLogin: unexpected error: " + resp.Status() + resp.String())
	}

	return resp, nil
}

func API_SetAccessTokenCookie(response *resty.Response) error {
	for _, s := range response.Cookies() {
		if s.Name == "access_token_cookie" {
			client.SetCookie(s)
			return nil
		}
	}
	return errors.New("no Access-Token-Cookie found")
}

func API_Wrong_SetAccessTokenCookie() {
	old_access_token_cookie := http.Cookie{
		Name:     "access_token_cookie",
		Value:    "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJpbnNlY3VyZUFkbWluTG9naW4iLCJpYXQiOjE2NzgyODIzNzgsIm5iZiI6MTY3ODI4MjM3OCwianRpIjoiNGIxOTlmY2MtNmFjNi00Y2IyLWI1M2ItNTM0MWUzNzNkMTkzIiwiZXhwIjoxNjc4MjgyNDM4LCJ0eXBlIjoiYWNjZXNzIiwiZnJlc2giOmZhbHNlLCJyb2xlIjpbImFkbWluIl19.-13AxRyWWxCRBFncZFnNisIdOVBF_dTrtMP6aGhqMGc",
		Path:     "/",
		HttpOnly: true,
	}
	client.SetCookie(&old_access_token_cookie)
}

func API_SetAccessTokenHeader_fromRespCookie(response *resty.Response) error {
	for _, s := range response.Cookies() {
		if s.Name == "access_token_cookie" {
			raw_token := s.Value
			client.SetAuthToken(raw_token)
			return nil
		}
	}
	return errors.New("no Access-Token-Cookie found")
}

func API_SetAccessTokenHeader_fromRespBody(respBody *TokenReply) error {
	raw_token := respBody.AccessToken
	client.SetAuthToken(raw_token)
	return nil
}

func API_SetRefreshTokenCookie(response *resty.Response) error {
	for _, s := range response.Cookies() {
		if s.Name == "refresh_token_cookie" {
			client.SetCookie(s)
			return nil
		}
	}
	return errors.New("no Refresh-Token-Cookie found")
}

func API_Wrong_SetRefreshTokenCookie() {
	old_refresh_token_cookie := http.Cookie{
		Name:     "refresh_token_cookie",
		Value:    "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJpbnNlY3VyZUFkbWluTG9naW4iLCJpYXQiOjE2NzgyMDQwMDYsIm5iZiI6MTY3ODIwNDAwNiwianRpIjoiNDdlN2I1NDYtOTgxOS00OGU5LTg5MDQtOTUzYTExOGI3NmZhIiwiZXhwIjoxNjc4MjExMjA2LCJ0eXBlIjoicmVmcmVzaCJ9.3J8mC3JpV4wV_LxcbV6Wt9UEeSuJpnous-rKXrvpuq8",
		Path:     "/",
		HttpOnly: true,
	}
	client.SetCookie(&old_refresh_token_cookie)
}

func API_SetRefreshTokenHeader_fromRespCookie(response *resty.Response) error {
	for _, s := range response.Cookies() {
		if s.Name == "refresh_token_cookie" {
			raw_token := s.Value
			client.SetAuthToken(raw_token)
			return nil
		}
	}
	return errors.New("no Access-Token-Cookie found")
}

func Register(newUserName string, newUserPW string, newUserMail string, newUserRole string) (*resty.Response, error) {
	registerBody := RegisterRequestBody{}
	registerBody.Email = newUserMail
	registerBody.Username = newUserName
	registerBody.Password = newUserPW
	registerBody.Role = newUserRole

	resp, err := client.R().
		SetHeader("Content-Type", "application/json").
		SetBody(registerBody).
		Post("login/register")
	if err != nil {
		log.Print(err.Error())
		return resp, err
	}
	if resp.StatusCode() == 403 {
		return resp, errors.New("Register: status 403 " + resp.String())
	} else if resp.StatusCode() != 200 {
		return resp, errors.New("Register: unexpected error: " + resp.Status() + resp.String())
	}
	return resp, nil
}

func Refresh() (*resty.Response, error) {

	resp, err := client.R().
		SetHeader("Content-Type", "application/json").
		Post("login/refresh")
	if err != nil {
		log.Print(err.Error())
		return resp, err
	}
	if resp.StatusCode() == 403 {
		return resp, errors.New("Refresh: status 403 " + resp.String())
	} else if resp.StatusCode() != 200 {
		return resp, errors.New("Refresh: unexpected error: " + resp.Status() + resp.String())
	}
	return resp, nil
}

func RefreshSensor() (*resty.Response, *TokenReply, error) {
	myTokenReply := TokenReply{}
	resp, err := client.R().
		SetHeader("Content-Type", "application/json").
		SetResult(&myTokenReply).
		Post("login/refresh")
	if err != nil {
		log.Print(err.Error())
		return resp, &myTokenReply, err
	}
	if resp.StatusCode() == 403 {
		return resp, &myTokenReply, errors.New("Refresh: status 403 " + resp.String())
	} else if resp.StatusCode() != 200 {
		return resp, &myTokenReply, errors.New("Refresh: unexpected error: " + resp.Status() + resp.String())
	}
	return resp, &myTokenReply, nil
}

func SensorToken(sensorName string) (*resty.Response, error) {
	sensorNameBody := SensorTokenRequestBody{}
	sensorNameBody.SensorName = sensorName

	resp, err := client.R().
		SetHeader("Content-Type", "application/json").
		SetBody(sensorNameBody).
		Post("login/sensor_token")
	if err != nil {
		log.Print(err.Error())
		return resp, err
	}
	if resp.StatusCode() == 403 {
		return resp, errors.New("Sensor_Token: status 403 " + resp.String())
	} else if resp.StatusCode() != 200 {
		return resp, errors.New("Sensor_Token: unexpected error: " + resp.Status() + resp.String())
	}
	return resp, nil
}

func Logout() (*resty.Response, error) {

	resp, err := client.R().
		SetHeader("Content-Type", "application/json").
		Delete("login/logout")
	if err != nil {
		log.Print(err.Error())
		return resp, err
	}
	if resp.StatusCode() == 403 {
		return resp, errors.New("Refresh: status 403 " + resp.String())
	} else if resp.StatusCode() != 200 {
		return resp, errors.New("Refresh: unexpected error: " + resp.Status() + resp.String())
	}
	return resp, nil
}

func DeleteUser(deleteUserName string, deleteUserMail string) (*resty.Response, error) {
	deleteBody := RegisterRequestBody{}
	deleteBody.Email = deleteUserMail
	deleteBody.Username = deleteUserName
	deleteBody.Password = "not important"
	deleteBody.Role = "not important"

	resp, err := client.R().
		SetHeader("Content-Type", "application/json").
		SetBody(deleteBody).
		Delete("login/delete_user")
	if err != nil {
		log.Print(err.Error())
		return resp, err
	}
	if resp.StatusCode() == 403 {
		return resp, errors.New("DeleteUser: status 403 " + resp.String())
	} else if resp.StatusCode() != 200 {
		return resp, errors.New("DeleteUser: unexpected error: " + resp.Status() + resp.String())
	}
	return resp, nil
}

func Basicauth_Register(newSensorName string, newSensorPW string) (*resty.Response, error) {
	registerBody := RegisterRequestBody{}
	registerBody.Email = "newSensorMail"
	registerBody.Username = newSensorName
	registerBody.Password = newSensorPW
	registerBody.Role = "newSensorRole"

	resp, err := client.R().
		SetHeader("Content-Type", "application/json").
		SetBody(registerBody).
		Post("login/basicauth_register")
	if err != nil {
		log.Print(err.Error())
		return resp, err
	}
	if resp.StatusCode() != 200 {
		return resp, errors.New("Basicauth_Register: unexpected error: " + resp.Status() + resp.String())
	}
	return resp, nil
}

func Basicauth_Delete(removeSensorName string) (*resty.Response, error) {
	deleteBody := RegisterRequestBody{}
	deleteBody.Email = "newSensorMail"
	deleteBody.Username = removeSensorName
	deleteBody.Password = "newSensorPW"
	deleteBody.Role = "newSensorRole"

	resp, err := client.R().
		SetHeader("Content-Type", "application/json").
		SetBody(deleteBody).
		Delete("login/basicauth_delete")
	if err != nil {
		log.Print(err.Error())
		return resp, err
	}
	if resp.StatusCode() != 200 {
		return resp, errors.New("Basicauth_Delete: unexpected error: " + resp.Status() + resp.String())
	}
	return resp, nil
}
