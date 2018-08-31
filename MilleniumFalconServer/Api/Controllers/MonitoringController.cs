using Microsoft.AspNetCore.Mvc;

namespace Api.Controllers
{
    [Route("monitoring")]
    public class MonitoringController : Controller
    {
        [HttpGet]
        public string Get()
        {
            return "Läuft!";
        }
    }
}
