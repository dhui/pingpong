$(document).ready(function() {
    $("#newPlayerForm").submit(function() {
        var playerName = $("#newPlayerName").val();
        $.ajax({
            url: "/players/",
            type: "POST",
            dataType: "json",
            processData: false,
            data: JSON.stringify({name: playerName}),
        }).success(function(response) {
            $("#players").append("<tr><td>" + playerName + '</td><td><input type="button" class="removePlayer" playerId="'
                                 + response.id + '" value="Remove"/></td></tr>');
            $("#newPlayerName").val("");
        }).error(function() {
            alert("Error adding player: " + playerName);
        });
        return false;
    });

    $(".removePlayer").live("click", function() {
        var input = $(this);
        var id = $(this).attr("playerId");
        $.ajax({
            url: "/players/",
            type: "DELETE",
            dataType: "json",
            processData: false,
            data: JSON.stringify({id: id}),
        }).success(function(response) {
            input.parent("td").parent("tr").remove();
        }).error(function() {
            alert("Error removing player: " + input.parent("td").prev().val());
        });
    });
});