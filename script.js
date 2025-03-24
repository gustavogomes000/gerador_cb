$(document).ready(function() {
    $("#barcodeForm").submit(function(event) {
        event.preventDefault();
        let formData = new FormData(this);
        fetch("/generate", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            $("#barcodeImage").attr("src", data.image_url);
            $("#downloadBtn").attr("href", data.image_url);
            $("#downloadBtn").attr("download", data.filename);
            $("#barcodeContainer").show();
        });
    });

    $("#autoBarcodeForm").submit(function(event) {
        event.preventDefault();
        let productName = $("#auto_product_name").val();
        let categoria = $("#categoria").val();
        if (!productName || !categoria) {
            alert("Por favor, preencha todos os campos.");
            return;
        }
        fetch("/generate_auto", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ product_name: productName, categoria: categoria })
        })
        .then(response => response.json())
        .then(data => {
            $("#barcodeImage").attr("src", data.image_url);
            $("#downloadBtn").attr("href", data.image_url);
            $("#downloadBtn").attr("download", data.filename);
            $("#barcodeContainer").show();
        });
    });

    $("#searchBtn").click(function() {
        let query = $("#searchQuery").val();
        fetch(`/search?query=${query}`)
        .then(response => response.json())
        .then(results => {
            let output = "";
            if (results.length > 0) {
                results.forEach(item => {
                    output += `<div class="text-center mb-3">
                        <h6>${item[0]}</h6>
                        <img src="/barcodes/${item[1]}" class="img-fluid">
                        <a href="/barcodes/${item[1]}" class="btn btn-success w-100 mt-2" download>Baixar</a>
                    </div>`;
                });
            } else {
                output = "<p class='text-center'>Nenhum resultado encontrado.</p>";
            }
            $("#searchResults").html(output);
        });
    });
});
