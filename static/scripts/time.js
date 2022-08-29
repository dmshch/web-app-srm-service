function updateTime() {
	$.ajax('/time',   // request url
		{
		  // success callback Function       
		  success: function (data, status, xhr) 
				{ 
					document.getElementById("time").innerHTML = data
				}

		}
	);
}
updateTime()
let timerIdTime = setInterval(() => updateTime(), 5000);