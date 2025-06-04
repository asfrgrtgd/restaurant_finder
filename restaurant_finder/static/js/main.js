    let map;
    let currentMarker;
    let restaurantMarkers = [];
    let currentPosition = { lat: 35.607, lng: 140.106 }; // デフォルト位置: 千葉市
    let isClickMode = false;
    let radiusCircle;

    // 地図の初期化
    function initMap() {
      map = L.map("map").setView([currentPosition.lat, currentPosition.lng], 15);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
      }).addTo(map);

      // マップクリック時、クリックモードが有効なら現在位置更新
      map.on("click", (e) => {
        if (isClickMode) {
          currentPosition = {
            lat: e.latlng.lat,
            lng: e.latlng.lng,
          };
          updateCurrentLocationMarker();
          searchRestaurants();
        }
      });

      updateCurrentLocationMarker();
    }

    // 現在位置マーカーの更新
    function updateCurrentLocationMarker() {
      if (currentMarker) {
        map.removeLayer(currentMarker);
      }

      const customIcon = L.icon({
        iconUrl:
          "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png",
        shadowUrl:
          "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41],
      });

      currentMarker = L.marker([currentPosition.lat, currentPosition.lng], {
        icon: customIcon,
        title: "選択位置",
      }).addTo(map);

      updateRadiusCircle();
    }

    // 検索半径の円を更新
    function updateRadiusCircle() {
      if (radiusCircle) {
        map.removeLayer(radiusCircle);
      }

      const radius = parseInt(document.getElementById("searchRadius").value);
      radiusCircle = L.circle([currentPosition.lat, currentPosition.lng], {
        radius: radius,
        className: "leaflet-circle-radius",
      }).addTo(map);

      // 円の範囲にあわせてマップを移動
      const bounds = radiusCircle.getBounds();
      map.fitBounds(bounds);
    }

    // レストランマーカーの更新
    function updateRestaurantMarkers(restaurants) {
      // 既存マーカーを除去
      restaurantMarkers.forEach((marker) => map.removeLayer(marker));
      restaurantMarkers = [];

      const restaurantIcon = L.icon({
        iconUrl:
          "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
        shadowUrl:
          "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41],
      });

      restaurants.forEach((restaurant) => {
        const marker = L.marker(
          [restaurant.location.lat, restaurant.location.lng],
          {
            icon: restaurantIcon,
            title: restaurant.name,
          }
        ).addTo(map);

        marker.bindPopup(`
          <div class="p-2">
            <h3 class="font-bold text-xl mb-1">${restaurant.name}</h3>
            <p class="text-gray-600">${restaurant.vicinity}</p>
            <div class="flex items-center mt-2">
              <span class="text-yellow-500 mr-1">★</span>
              <span>${restaurant.rating}</span>
              <span class="ml-2 text-blue-500">${restaurant.distance}m</span>
            </div>
          </div>
        `);

        restaurantMarkers.push(marker);
      });
    }

    // レストラン情報の表示
    function displayRestaurants(restaurants) {
      const container = document.getElementById("restaurantList");
      const resultCount = document.getElementById("resultCount");
      container.innerHTML = "";

      if (!restaurants || restaurants.length === 0) {
        resultCount.textContent = "この範囲にレストランは見つかりませんでした";
        // レストランがない場合のメッセージ
        const noResultsMessage = document.createElement("div");
        noResultsMessage.className = "text-center p-8 bg-gray-50 rounded-xl shadow-sm";
        noResultsMessage.innerHTML = `
          <i class="fas fa-search text-4xl text-gray-400 mb-4"></i>
          <p class="text-gray-600">検索範囲を広げてみてください</p>
        `;
        container.appendChild(noResultsMessage);
        return;
      }

      resultCount.textContent = `${restaurants.length}件のレストランが見つかりました`;

      restaurants.forEach((restaurant) => {
        const card = document.createElement("div");
        card.className = "card bg-white rounded-xl shadow-lg overflow-hidden";

        // 星の数を生成
        // 例: 評価3.7 → ★★★★(3+0.7→半分)
        const fullStars = Math.floor(restaurant.rating);
        const halfStar = restaurant.rating - fullStars >= 0.5;
        const starsHTML = Array(fullStars)
          .fill()
          .map(() => '<i class="fas fa-star text-yellow-400 text-xl"></i>')
          .join("");
        const halfStarHTML = halfStar
          ? '<i class="fas fa-star-half-alt text-yellow-400 text-xl"></i>'
          : "";

        // rating が 0 の場合は「評価なし」にする例
        const ratingDisplay = restaurant.rating > 0
          ? `${starsHTML}${halfStarHTML} <span class="ml-2 text-gray-600 text-lg">${restaurant.rating}</span>`
          : '評価なし';

        card.innerHTML = `
          <div class="p-6">
            <div class="flex justify-between items-start mb-4">
              <h3 class="text-2xl font-semibold text-gray-800 flex-1">${restaurant.name}</h3>
              <span class="bg-blue-100 text-blue-800 text-sm font-medium px-2.5 py-0.5 rounded-full">
                ${restaurant.distance}m
              </span>
            </div>
            <p class="text-gray-600 mb-4 flex items-start">
              <i class="fas fa-location-dot text-gray-400 mr-2 mt-1"></i>
              <span>${restaurant.vicinity}</span>
            </p>
            <div class="flex items-center justify-between">
              <div class="flex items-center">
                ${ratingDisplay}
              </div>
              <button
                onclick="map.setView([${restaurant.location.lat}, ${restaurant.location.lng}], 18)"
                class="text-blue-500 hover:text-blue-600 transition-colors duration-200"
              >
                <i class="fas fa-map-marked-alt"></i>
              </button>
            </div>
          </div>
        `;
        container.appendChild(card);
      });
    }

    // レストランの検索
    async function searchRestaurants() {
      const loadingIndicator = document.getElementById("loadingIndicator");
      loadingIndicator.classList.remove("hidden");

      try {
        const radius = document.getElementById("searchRadius").value;
        const response = await fetch("/search_restaurants", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            lat: currentPosition.lat,
            lng: currentPosition.lng,
            radius: radius,
          }),
        });

        const data = await response.json();
        if (data.error) {
          showError(data.error);
          return;
        }

        displayRestaurants(data.restaurants || []);
        updateRestaurantMarkers(data.restaurants || []);
        updateRadiusCircle();
      } catch (error) {
        console.error("Error:", error);
        showError("予期せぬエラーが発生しました");
      } finally {
        loadingIndicator.classList.add("hidden");
      }
    }

    // エラー表示
    function showError(message) {
      const container = document.getElementById("restaurantList");
      const resultCount = document.getElementById("resultCount");
      container.innerHTML = "";
      resultCount.textContent = "エラーが発生しました";

      const errorMessage = document.createElement("div");
      errorMessage.className = "text-center p-8 bg-red-50 rounded-xl shadow-sm";
      errorMessage.innerHTML = `
        <i class="fas fa-exclamation-circle text-4xl text-red-400 mb-4"></i>
        <p class="text-red-600">${message}</p>
        <p class="text-gray-600 mt-2">検索半径を調整してもう一度お試しください</p>
      `;
      container.appendChild(errorMessage);
    }

    // 現在地の取得
    document
      .getElementById("getCurrentLocation")
      .addEventListener("click", async () => {
        try {
          const response = await fetch("/get_current_location");
          const data = await response.json();

          if (data.error) {
            throw new Error(data.error);
          }

          currentPosition = {
            lat: data.location.lat,
            lng: data.location.lng,
          };

          updateCurrentLocationMarker();
          searchRestaurants();
        } catch (error) {
          console.error("Error:", error);
          alert("現在地の取得に失敗しました: " + error.message);
        }
      });

    // クリックモードの切り替え
    document.getElementById("toggleClickMode").addEventListener("click", () => {
      isClickMode = !isClickMode;
      const button = document.getElementById("toggleClickMode");
      const pinText = button.querySelector(".pin-text");
      const tooltip = button.querySelector(".pin-tooltip");

      if (isClickMode) {
        // アクティブモード
        button.classList.remove("bg-green-500", "hover:bg-green-600");
        button.classList.add("bg-yellow-500", "hover:bg-yellow-600", "click-mode-active");
        pinText.textContent = "クリックモード終了";
        button.querySelector("i").className = "fas fa-times mr-2";
        map.getContainer().style.cursor = "crosshair";

        // モバイル向けツールチップ表示
        if (window.innerWidth <= 768) {
          tooltip.style.opacity = "1";
          tooltip.style.visibility = "visible";
          setTimeout(() => {
            tooltip.style.opacity = "0";
            tooltip.style.visibility = "hidden";
          }, 3000);
        }
      } else {
        // 通常モード
        button.classList.remove("bg-yellow-500", "hover:bg-yellow-600", "click-mode-active");
        button.classList.add("bg-green-500", "hover:bg-green-600");
        pinText.textContent = "ピンを追加";
        button.querySelector("i").className = "fas fa-map-pin mr-2";
        map.getContainer().style.cursor = "";
      }
    });

    // 検索半径変更時の処理
    document.getElementById("searchRadius").addEventListener("change", () => {
      updateRadiusCircle();
      searchRestaurants();
    });

    // ページ読み込み時にマップ初期化 & 初回検索
    initMap();
    searchRestaurants();
