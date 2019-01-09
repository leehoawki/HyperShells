package main

import (
	"fmt"
	"github.com/akamensky/argparse"
	"github.com/labstack/echo"
	"github.com/labstack/echo/middleware"
	"io/ioutil"
	"net/http"
	"os"
	"strings"
)

func main() {
	e := echo.New()
	parser := argparse.NewParser("simplehttpserver", "Simple Http Server ...")
	p := parser.String("p", "int", &argparse.Options{Required: false, Default: "8000", Help: "port"})
	err := parser.Parse(os.Args)
	if err != nil {
		fmt.Print(parser.Usage(err))
	}

	e.Use(middleware.Logger())
	e.Use(middleware.Recover())

	e.GET("/*", screw)

	var port = ":"
	port += *p
	e.Logger.Info(e.Start(port))
}

func screw(c echo.Context) error {
	p := c.Request().RequestURI
	var path = "./"
	if len(p) > 1 {
		path = p[1:]
	}
	if isFile(path) {
		content, e := ioutil.ReadFile(path)
		if e == nil {
			if strings.HasSuffix(path, "html") {
				return c.Blob(http.StatusOK, "text/html", content)
			}
			return c.Blob(http.StatusOK, "text/plain", content)
		} else {
			return c.HTML(http.StatusOK, e.Error())
		}
	} else if strings.HasSuffix(path, "/") {
		return c.HTML(http.StatusOK, listFile(path))
	} else {
		print(path)
		return c.Redirect(http.StatusFound, p+"/")
	}
}

func isFile(f string) bool {
	fi, e := os.Stat(f)
	if e != nil {
		return false
	}
	return !fi.IsDir()
}

func listFile(f string) string {
	output := fmt.Sprintf(`
    <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
    <html>
    <title>Directory listing for %s</title>
    <body>
    <h2>Directory listing for %s</h2>
    <hr>
    <ul>
`, f, f)

	dir, err := ioutil.ReadDir(f)
	if err != nil {
		panic(err)
	}

	for _, fi := range dir {
		if fi.IsDir() {
			output += fmt.Sprintf(`
            <li><a href="./%s/">%s</a>
                `, fi.Name(), fi.Name())
		} else {
			output += fmt.Sprintf(`
            <li><a href="./%s">%s</a>
                `, fi.Name(), fi.Name())
		}
	}

	output += `
    </ul>
    </hr>
    </body>
    </html>
`
	return output
}
