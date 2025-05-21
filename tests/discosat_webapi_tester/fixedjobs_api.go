package discosat_webapi_tester

import (
	"errors"
	"github.com/go-resty/resty/v2"
	"log"
	"strings"
)

type FixedJob struct {
	Id        string            `json:"id"`
	Name      string            `json:"name"`
	StartTime int64             `json:"start_time"`
	EndTime   int64             `json:"end_time"`
	Command   string            `json:"command"`
	Arguments map[string]string `json:"arguments"`
	Sensors   []string          `json:"sensors"`
	Status    string            `json:"status"`
	States    map[string]string `json:"states"`
}

type FixedJobResponse struct {
	Data    []FixedJob
	Code    int
	Message string
}

func GetJobs(sensorName string) (*resty.Response, []FixedJob, error) {
	respCont := FixedJobResponse{}
	resp, err := client.R().
		SetHeader("Accept", "application/json").
		SetResult(&respCont).
		Get("fixedjobs/" + sensorName)
	if err != nil {
		log.Print(err.Error())
		return resp, []FixedJob{}, err
	} else if resp.StatusCode() != 200 {
		return resp, respCont.Data, errors.New("GetJobs.ResponseStatus = " + resp.Status())
	}
	if strings.Contains(resp.String(), "error") {
		return resp, respCont.Data, errors.New("GetJobs.Response-internal error: " + resp.String())
	}
	return resp, respCont.Data, nil
}
