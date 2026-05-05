<template>
  <div class="weather-view">
    <div class="weather-main">
      <div class="weather-header">
        <div class="city-search">
          <div class="search-input-wrap">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
            <input
              v-model="searchQuery"
              placeholder="Search city..."
              @input="onSearchInput"
              @keydown.enter="searchCity"
            />
          </div>
          <div v-if="searchResults.length" class="search-dropdown">
            <div
              v-for="city in searchResults"
              :key="city.id"
              class="search-item"
              @click="selectCity(city)"
            >
              <span class="city-name">{{ city.name }}</span>
              <span class="city-detail">{{ city.admin1 }}, {{ city.country }}</span>
            </div>
          </div>
        </div>
        <div v-if="currentCity" class="current-city">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
          <span>{{ currentCity.name }}, {{ currentCity.country }}</span>
        </div>
        <div class="ai-header-group">
          <button class="ai-header-btn" @click="aiOutfitSuggest">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.38 3.46L16 2 12 5.5 8 2l-4.38 1.46a1 1 0 00-.62.94V19a1 1 0 001 1h16a1 1 0 001-1V4.4a1 1 0 00-.62-.94z"/></svg>
            Outfit
          </button>
          <button class="ai-header-btn" @click="aiTravelAdvice">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>
            Travel
          </button>
          <button class="ai-header-btn" @click="aiScheduleAdjust">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
            Schedule
          </button>
          <button class="ai-header-btn" @click="aiHealthTip">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>
            Health
          </button>
        </div>
      </div>

      <div v-if="loading" class="weather-loading">
        <div class="spinner"></div>
        <span>Loading weather data...</span>
      </div>

      <div v-else-if="forecast" class="weather-content">
        <div class="current-section">
          <div class="current-main">
            <div class="weather-icon-large" v-html="getWeatherSvg(forecast.current.weather_icon, forecast.current.is_day)"></div>
            <div class="current-temp">
              <span class="temp-value">{{ Math.round(forecast.current.temperature) }}</span>
              <span class="temp-unit">&deg;C</span>
            </div>
            <div class="current-desc">{{ forecast.current.weather_label }}</div>
          </div>
          <div class="current-details">
            <div class="detail-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 14.76V3.5a2.5 2.5 0 00-5 0v11.26a4.5 4.5 0 105 0z"/></svg>
              <span>Feels like {{ Math.round(forecast.current.feels_like) }}&deg;</span>
            </div>
            <div class="detail-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2.69l5.66 5.66a8 8 0 11-11.31 0z"/></svg>
              <span>Humidity {{ forecast.current.humidity }}%</span>
            </div>
            <div class="detail-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9.59 4.59A2 2 0 1111 8H2m10.59 11.41A2 2 0 1014 16H2m15.73-8.27A2.5 2.5 0 1119.5 12H2"/></svg>
              <span>{{ forecast.current.wind_direction_label }} {{ forecast.current.wind_speed }} km/h</span>
            </div>
            <div class="detail-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v6m0 8v6M2 12h6m8 0h6"/></svg>
              <span>Pressure {{ forecast.current.pressure }} hPa</span>
            </div>
            <div class="detail-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.5 19H9a7 7 0 010-14h.5"/></svg>
              <span>Cloud {{ forecast.current.cloud_cover }}%</span>
            </div>
            <div class="detail-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2.69l5.66 5.66a8 8 0 11-11.31 0z"/></svg>
              <span>Precip {{ forecast.current.precipitation }} mm</span>
            </div>
          </div>
          <div v-if="airQuality" class="air-quality-section">
            <div class="aqi-badge" :class="aqiLevel">{{ Math.round(airQuality.us_aqi) }}</div>
            <div class="aqi-info">
              <span class="aqi-label">AQI {{ aqiLabel }}</span>
              <span class="aqi-detail">PM2.5: {{ airQuality.pm2_5?.toFixed(1) }} | PM10: {{ airQuality.pm10?.toFixed(1) }}</span>
            </div>
          </div>
        </div>

        <div class="hourly-section">
          <h4 class="section-title">24h Forecast</h4>
          <div class="hourly-scroll">
            <div v-for="h in todayHourly" :key="h.time" class="hourly-item">
              <span class="hourly-time">{{ formatHour(h.time) }}</span>
              <div class="hourly-icon" v-html="getWeatherSvg(h.weather_icon, 1)"></div>
              <span class="hourly-temp">{{ Math.round(h.temperature) }}&deg;</span>
              <span v-if="h.precipitation_probability > 0" class="hourly-precip">{{ h.precipitation_probability }}%</span>
            </div>
          </div>
        </div>

        <div class="daily-section">
          <h4 class="section-title">7-Day Forecast</h4>
          <div class="daily-list">
            <div v-for="d in forecast.daily" :key="d.date" class="daily-item">
              <span class="daily-day">{{ formatDay(d.date) }}</span>
              <div class="daily-icon" v-html="getWeatherSvg(d.weather_icon, 1)"></div>
              <span class="daily-label">{{ d.weather_label }}</span>
              <div class="daily-temp-bar">
                <span class="daily-min">{{ Math.round(d.temp_min) }}&deg;</span>
                <div class="temp-bar">
                  <div class="temp-bar-fill" :style="tempBarStyle(d)"></div>
                </div>
                <span class="daily-max">{{ Math.round(d.temp_max) }}&deg;</span>
              </div>
              <div class="daily-extras">
                <span v-if="d.precipitation_probability > 0" class="daily-precip">{{ d.precipitation_probability }}%</span>
                <span class="daily-wind">{{ Math.round(d.wind_speed_max) }} km/h</span>
              </div>
            </div>
          </div>
        </div>

        <div class="sun-section" v-if="forecast.daily.length">
          <div class="sun-info">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--ws-warning)" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
            <span>Sunrise {{ formatTime(forecast.daily[0].sunrise) }}</span>
          </div>
          <div class="sun-info">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ff6b35" stroke-width="2"><path d="M17 18a5 5 0 00-10 0"/><path d="M12 2v7M4.22 10.22l1.42 1.42M1 18h2M21 18h2M18.36 11.64l1.42-1.42M23 22H1"/></svg>
            <span>Sunset {{ formatTime(forecast.daily[0].sunset) }}</span>
          </div>
          <div class="sun-info" v-if="forecast.daily[0].uv_index != null">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ff6b6b" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
            <span>UV Index {{ forecast.daily[0].uv_index }}</span>
          </div>
        </div>
      </div>

      <div v-else class="weather-empty">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M17.5 19H9a7 7 0 010-14h.5A5.5 5.5 0 0117 6.5a5 5 0 014 2.5 3.5 3.5 0 010 7h-.5"/></svg>
        <p>Search for a city to view weather</p>
      </div>
    </div>

    <div v-if="showAIPanel" class="ai-panel">
      <div class="ai-panel-header">
        <h4>AI Weather Assistant</h4>
        <button class="close-btn" @click="showAIPanel = false">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="ai-panel-content">
        <div v-if="aiLoading" class="ai-loading">
          <div class="spinner"></div>
          <span>AI is analyzing...</span>
        </div>
        <div v-else-if="aiResult" class="ai-result">
          <div v-if="aiResult.outfit" class="ai-section">
            <h5>Outfit Suggestion</h5>
            <div class="outfit-card">
              <div v-if="aiResult.outfit.top" class="outfit-item"><span class="outfit-label">Top:</span> {{ aiResult.outfit.top }}</div>
              <div v-if="aiResult.outfit.bottom" class="outfit-item"><span class="outfit-label">Bottom:</span> {{ aiResult.outfit.bottom }}</div>
              <div v-if="aiResult.outfit.outerwear" class="outfit-item"><span class="outfit-label">Outerwear:</span> {{ aiResult.outfit.outerwear }}</div>
              <div v-if="aiResult.outfit.accessories?.length" class="outfit-item"><span class="outfit-label">Accessories:</span> {{ aiResult.outfit.accessories.join(', ') }}</div>
              <div v-if="aiResult.outfit.tip" class="outfit-tip">{{ aiResult.outfit.tip }}</div>
            </div>
          </div>
          <div v-if="aiResult.advice" class="ai-section">
            <h5>Travel Advice</h5>
            <p class="advice-text">{{ aiResult.advice }}</p>
            <div v-if="aiResult.precautions?.length" class="precautions">
              <h6>Precautions</h6>
              <div v-for="(p, i) in aiResult.precautions" :key="i" class="precaution-item">{{ p }}</div>
            </div>
            <div v-if="aiResult.best_time" class="best-time">Best time: {{ aiResult.best_time }}</div>
            <div v-if="aiResult.transport_tips" class="transport-tips">Transport: {{ aiResult.transport_tips }}</div>
          </div>
          <div v-if="aiResult.adjustments?.length" class="ai-section">
            <h5>Schedule Adjustments</h5>
            <div v-for="(a, i) in aiResult.adjustments" :key="i" class="adjustment-item">
              <div class="adj-original">{{ a.original_plan }}</div>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
              <div class="adj-suggested">{{ a.suggested_change }}</div>
              <div class="adj-reason">{{ a.reason }}</div>
            </div>
            <div v-if="aiResult.indoor_alternatives?.length" class="indoor-alt">
              <h6>Indoor Alternatives</h6>
              <div v-for="(alt, i) in aiResult.indoor_alternatives" :key="i" class="alt-item">{{ alt }}</div>
            </div>
          </div>
          <div v-if="aiResult.tips?.length" class="ai-section">
            <h5>Health Tips</h5>
            <div v-for="(t, i) in aiResult.tips" :key="i" :class="['health-tip', `priority-${t.priority}`]">
              <span class="tip-category">{{ t.category }}</span>
              <span class="tip-advice">{{ t.advice }}</span>
            </div>
            <div v-if="aiResult.warnings?.length" class="warnings">
              <div v-for="(w, i) in aiResult.warnings" :key="i" class="warning-item">{{ w }}</div>
            </div>
          </div>
          <div v-if="aiResult.result && !aiResult.outfit && !aiResult.advice && !aiResult.adjustments && !aiResult.tips" class="ai-section">
            <p>{{ aiResult.result }}</p>
          </div>
        </div>
        <div v-else class="ai-empty">
          <p>Use AI to get outfit suggestions, travel advice, schedule adjustments, or health tips based on weather</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '../../utils/api'
import type { WeatherForecast, WeatherCity, AirQuality } from '../../types/workspace'
import { useAppSettings } from '@/composables/useAppSettings'
import { useSettings } from '@/composables/useSettings'

const { settings: weatherSettings } = useAppSettings('weather')
const { updateApp } = useSettings()

const searchQuery = ref('')
const searchResults = ref<WeatherCity[]>([])
const currentCity = ref<WeatherCity | null>(null)
const forecast = ref<WeatherForecast | null>(null)
const airQuality = ref<AirQuality | null>(null)
const loading = ref(false)
const showAIPanel = ref(false)
const aiLoading = ref(false)
const aiResult = ref<any>(null)

let searchTimer: ReturnType<typeof setTimeout> | null = null

const WEATHER_SVG_MAP: Record<string, string> = {
  'clear': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--ws-warning)" stroke-width="1.5"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>',
  'mostly-clear': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--ws-warning)" stroke-width="1.5"><circle cx="10" cy="10" r="4"/><path d="M10 2v1M10 18v1M3 10H2M18 10h1M4.93 4.93l.7.7M14.36 14.36l.7.7"/><path d="M16 16a4 4 0 01-4-4 4 4 0 01-4 4" stroke="#ccc" opacity="0.5"/></svg>',
  'partly-cloudy': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke-width="1.5"><circle cx="10" cy="8" r="3.5" stroke="var(--ws-warning)"/><path d="M17 16h.5a3.5 3.5 0 000-7h-.2a5 5 0 00-9.8 1.5A3.5 3.5 0 008 16h9z" stroke="#ccc"/></svg>',
  'overcast': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="1.5"><path d="M18 16h.5a3.5 3.5 0 000-7h-.2a5 5 0 00-9.8 1.5A3.5 3.5 0 009 16h9z"/><path d="M6 19h12a3 3 0 000-6h-.1a4 4 0 00-7.8-1A3 3 0 006 16v3z" opacity="0.6"/></svg>',
  'fog': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="1.5"><path d="M3 15h18M3 11h18M3 19h18M5 7h14" opacity="0.5"/></svg>',
  'drizzle': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke-width="1.5"><path d="M16 12h.5a3.5 3.5 0 000-7h-.2a5 5 0 00-9.8 1.5A3.5 3.5 0 008 12h8z" stroke="#ccc"/><path d="M8 16v2M12 16v2M16 16v2" stroke="var(--ws-info)" stroke-width="1"/></svg>',
  'rain': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke-width="1.5"><path d="M16 10h.5a3.5 3.5 0 000-7h-.2a5 5 0 00-9.8 1.5A3.5 3.5 0 008 10h8z" stroke="#ccc"/><path d="M7 14l-1 4M11 14l-1 4M15 14l-1 4" stroke="var(--ws-info)" stroke-width="1.5"/></svg>',
  'heavy-rain': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke-width="1.5"><path d="M16 8h.5a3.5 3.5 0 000-7h-.2a5 5 0 00-9.8 1.5A3.5 3.5 0 008 8h8z" stroke="#999"/><path d="M6 12l-1.5 5M10 12l-1.5 5M14 12l-1.5 5M18 12l-1.5 5" stroke="#4a8eff" stroke-width="1.5"/></svg>',
  'snow': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#b8d4ff" stroke-width="1.5"><path d="M16 10h.5a3.5 3.5 0 000-7h-.2a5 5 0 00-9.8 1.5A3.5 3.5 0 008 10h8z" stroke="#ccc"/><path d="M8 16l-1 3M12 15l-1 4M16 16l-1 3" stroke="#b8d4ff"/></svg>',
  'heavy-snow': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#b8d4ff" stroke-width="1.5"><path d="M16 8h.5a3.5 3.5 0 000-7h-.2a5 5 0 00-9.8 1.5A3.5 3.5 0 008 8h8z" stroke="#999"/><path d="M6 12l-1 4M10 12l-1 4M14 12l-1 4M18 12l-1 4" stroke="#b8d4ff" stroke-width="1.5"/></svg>',
  'thunderstorm': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke-width="1.5"><path d="M16 8h.5a3.5 3.5 0 000-7h-.2a5 5 0 00-9.8 1.5A3.5 3.5 0 008 8h8z" stroke="#999"/><path d="M11 12l-2 6h4l-2 6" stroke="#ffcc00" stroke-width="2"/></svg>',
  'freezing-rain': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke-width="1.5"><path d="M16 10h.5a3.5 3.5 0 000-7h-.2a5 5 0 00-9.8 1.5A3.5 3.5 0 008 10h8z" stroke="#ccc"/><path d="M7 14l-1 4M11 14l-1 4M15 14l-1 4" stroke="#88ccff" stroke-width="1.5"/></svg>',
  'freezing-drizzle': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke-width="1.5"><path d="M16 12h.5a3.5 3.5 0 000-7h-.2a5 5 0 00-9.8 1.5A3.5 3.5 0 008 12h8z" stroke="#ccc"/><path d="M8 16v2M12 16v2M16 16v2" stroke="#88ccff" stroke-width="1"/></svg>',
  'rain-showers': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke-width="1.5"><circle cx="10" cy="8" r="3.5" stroke="var(--ws-warning)" opacity="0.5"/><path d="M16 12h.5a3.5 3.5 0 000-7h-.2a5 5 0 00-9.8 1.5A3.5 3.5 0 008 12h8z" stroke="#ccc"/><path d="M8 16v2M12 16v2" stroke="var(--ws-info)" stroke-width="1"/></svg>',
  'heavy-rain-showers': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke-width="1.5"><circle cx="10" cy="8" r="3.5" stroke="var(--ws-warning)" opacity="0.5"/><path d="M16 10h.5a3.5 3.5 0 000-7h-.2a5 5 0 00-9.8 1.5A3.5 3.5 0 008 10h8z" stroke="#999"/><path d="M7 14l-1 4M11 14l-1 4M15 14l-1 4" stroke="#4a8eff" stroke-width="1.5"/></svg>',
  'snow-showers': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke-width="1.5"><circle cx="10" cy="8" r="3.5" stroke="var(--ws-warning)" opacity="0.5"/><path d="M16 12h.5a3.5 3.5 0 000-7h-.2a5 5 0 00-9.8 1.5A3.5 3.5 0 008 12h8z" stroke="#ccc"/><path d="M8 16v2M12 16v2" stroke="#b8d4ff" stroke-width="1"/></svg>',
  'thunderstorm-hail': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke-width="1.5"><path d="M16 8h.5a3.5 3.5 0 000-7h-.2a5 5 0 00-9.8 1.5A3.5 3.5 0 008 8h8z" stroke="#999"/><path d="M11 12l-2 6h4l-2 6" stroke="#ffcc00" stroke-width="2"/><circle cx="7" cy="18" r="1.5" fill="#b8d4ff" stroke="none"/></svg>',
  'unknown': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17h.01"/></svg>',
}

function getWeatherSvg(icon: string, isDay: number): string {
  if (!isDay && (icon === 'clear' || icon === 'mostly-clear')) {
    return '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#c9d1ff" stroke-width="1.5"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>'
  }
  return WEATHER_SVG_MAP[icon] || WEATHER_SVG_MAP['unknown']
}

const todayHourly = computed(() => {
  if (!forecast.value?.hourly) return []
  const now = new Date()
  const todayStr = now.toISOString().slice(0, 10)
  return forecast.value.hourly.filter(h => {
    const hDate = h.time.slice(0, 10)
    const hHour = parseInt(h.time.slice(11, 13))
    return hDate === todayStr && hHour >= now.getHours()
  }).slice(0, 24)
})

const aqiLevel = computed(() => {
  if (!airQuality.value?.us_aqi) return 'good'
  const aqi = airQuality.value.us_aqi
  if (aqi <= 50) return 'good'
  if (aqi <= 100) return 'moderate'
  if (aqi <= 150) return 'unhealthy-sensitive'
  if (aqi <= 200) return 'unhealthy'
  return 'very-unhealthy'
})

const aqiLabel = computed(() => {
  const map: Record<string, string> = {
    'good': 'Good',
    'moderate': 'Moderate',
    'unhealthy-sensitive': 'Unhealthy (Sensitive)',
    'unhealthy': 'Unhealthy',
    'very-unhealthy': 'Very Unhealthy',
  }
  return map[aqiLevel.value] || 'Unknown'
})

function formatHour(time: string): string {
  const h = parseInt(time.slice(11, 13))
  return `${h}:00`
}

function formatDay(date: string): string {
  const d = new Date(date + 'T00:00:00')
  const today = new Date()
  if (d.toDateString() === today.toDateString()) return 'Today'
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)
  if (d.toDateString() === tomorrow.toDateString()) return 'Tomorrow'
  return d.toLocaleDateString('en', { weekday: 'short' })
}

function formatTime(time: string): string {
  if (!time) return ''
  return time.slice(11, 16)
}

function tempBarStyle(d: any) {
  if (!forecast.value?.daily?.length) return {}
  const allMin = Math.min(...forecast.value.daily.map((x: any) => x.temp_min))
  const allMax = Math.max(...forecast.value.daily.map((x: any) => x.temp_max))
  const range = allMax - allMin || 1
  const left = ((d.temp_min - allMin) / range) * 100
  const right = ((d.temp_max - allMin) / range) * 100
  return {
    left: `${left}%`,
    width: `${right - left}%`,
  }
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  searchTimer = setTimeout(searchCity, 400)
}

async function searchCity() {
  if (!searchQuery.value.trim()) return
  try {
    const res = await api.post('/ai/workspace/weather/search', {
      name: searchQuery.value,
      count: 5,
      language: 'zh',
    })
    searchResults.value = res.data.results || []
  } catch {
    searchResults.value = []
  }
}

async function selectCity(city: WeatherCity) {
  currentCity.value = city
  searchResults.value = []
  searchQuery.value = ''
  await loadWeather()
}

async function loadWeather() {
  if (!currentCity.value) return
  loading.value = true
  try {
    const [forecastRes, aqRes] = await Promise.allSettled([
      api.post('/ai/workspace/weather/forecast', {
        latitude: currentCity.value.latitude,
        longitude: currentCity.value.longitude,
        forecast_days: 7,
      }),
      api.post('/ai/workspace/weather/air-quality', {
        latitude: currentCity.value.latitude,
        longitude: currentCity.value.longitude,
      }),
    ])
    if (forecastRes.status === 'fulfilled') {
      forecast.value = forecastRes.value.data
    }
    if (aqRes.status === 'fulfilled') {
      airQuality.value = aqRes.value.data
    }
  } catch {
    forecast.value = null
    airQuality.value = null
  } finally {
    loading.value = false
  }
}

function buildWeatherContext(): string {
  if (!forecast.value?.current) return 'No weather data available'
  const c = forecast.value.current
  const today = forecast.value.daily?.[0]
  let ctx = `Current weather: ${c.weather_label} (${c.weather_label_en}), Temperature: ${c.temperature}°C (feels like ${c.feels_like}°C), Humidity: ${c.humidity}%, Wind: ${c.wind_direction_label} ${c.wind_speed}km/h, Precipitation: ${c.precipitation}mm, Cloud cover: ${c.cloud_cover}%`
  if (today) {
    ctx += `\nToday: High ${today.temp_max}°C, Low ${today.temp_min}°C, Precipitation probability: ${today.precipitation_probability}%, UV Index: ${today.uv_index}`
  }
  if (airQuality.value) {
    ctx += `\nAir Quality: AQI ${airQuality.value.us_aqi}, PM2.5: ${airQuality.value.pm2_5}, PM10: ${airQuality.value.pm10}`
  }
  return ctx
}

async function aiOutfitSuggest() {
  if (!forecast.value) return
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/weather/assist', {
      action: 'outfit_suggest',
      params: { weather_context: buildWeatherContext() },
    })
    aiResult.value = res.data
  } catch { aiResult.value = { result: 'Failed to get outfit suggestion.' } }
  finally { aiLoading.value = false }
}

async function aiTravelAdvice() {
  if (!forecast.value) return
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/weather/assist', {
      action: 'travel_advice',
      params: { weather_context: buildWeatherContext() },
    })
    aiResult.value = res.data
  } catch { aiResult.value = { result: 'Failed to get travel advice.' } }
  finally { aiLoading.value = false }
}

async function aiScheduleAdjust() {
  if (!forecast.value) return
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/weather/assist', {
      action: 'schedule_adjust',
      params: { weather_context: buildWeatherContext() },
    })
    aiResult.value = res.data
  } catch { aiResult.value = { result: 'Failed to get schedule adjustment.' } }
  finally { aiLoading.value = false }
}

async function aiHealthTip() {
  if (!forecast.value) return
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/weather/assist', {
      action: 'health_tip',
      params: { weather_context: buildWeatherContext() },
    })
    aiResult.value = res.data
  } catch { aiResult.value = { result: 'Failed to get health tips.' } }
  finally { aiLoading.value = false }
}

onMounted(() => {
  const ws = weatherSettings.value
  if (ws.cityId && ws.cityName) {
    currentCity.value = {
      id: ws.cityId,
      name: ws.cityName,
      country: ws.country || '',
      latitude: 0,
      longitude: 0,
    } as WeatherCity
    loadWeather()
  }
})

import { watch as vueWatch } from 'vue'
vueWatch(currentCity, (city) => {
  if (city) {
    updateApp({
      weather: {
        cityId: city.id,
        cityName: city.name,
        country: city.country,
      },
    })
  }
}, { deep: true })
</script>

<style scoped>
.weather-view { display: flex; height: 100%; background: var(--bg-primary); color: var(--text-primary); }
.weather-main { flex: 1; display: flex; flex-direction: column; overflow-y: auto; }
.weather-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-bottom: 1px solid var(--border-color); flex-wrap: wrap; }
.city-search { position: relative; }
.search-input-wrap { display: flex; align-items: center; gap: 6px; padding: 6px 10px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 6px; }
.search-input-wrap svg { color: var(--text-tertiary); flex-shrink: 0; }
.search-input-wrap input { background: none; border: none; color: var(--text-primary); font-size: 13px; outline: none; width: 160px; }
.search-input-wrap input::placeholder { color: var(--text-tertiary); }
.search-dropdown { position: absolute; top: 100%; left: 0; width: 260px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 6px; margin-top: 4px; z-index: 100; max-height: 240px; overflow-y: auto; }
.search-item { padding: 8px 12px; cursor: pointer; border-bottom: 1px solid var(--border-color); }
.search-item:last-child { border-bottom: none; }
.search-item:hover { background: var(--ws-accent-light); }
.city-name { font-size: 13px; color: var(--text-primary); display: block; }
.city-detail { font-size: 11px; color: var(--text-tertiary); }
.current-city { display: flex; align-items: center; gap: 4px; font-size: 14px; color: var(--ws-accent-soft); font-weight: 600; }
.ai-header-group { display: flex; gap: 6px; margin-left: auto; }
.ai-header-btn { display: flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 6px; font-size: 11px; color: var(--ws-accent); background: none; border: 1px solid var(--border-color); cursor: pointer; }
.ai-header-btn:hover { background: var(--ws-accent-light); border-color: var(--ws-accent); }
.weather-loading { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 48px; color: var(--text-tertiary); }
.spinner { width: 28px; height: 28px; border: 3px solid var(--border-color); border-top-color: var(--ws-accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.weather-content { padding: 16px; display: flex; flex-direction: column; gap: 20px; }
.current-section { display: flex; flex-direction: column; align-items: center; gap: 16px; padding: 24px; background: var(--bg-secondary); border-radius: 12px; }
.current-main { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.current-temp { display: flex; align-items: flex-start; }
.temp-value { font-size: 56px; font-weight: 200; line-height: 1; color: var(--text-primary); }
.temp-unit { font-size: 20px; color: var(--text-tertiary); margin-top: 8px; }
.current-desc { font-size: 16px; color: var(--ws-accent-soft); }
.current-details { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px 16px; }
.detail-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #999; }
.detail-item svg { color: var(--ws-accent); flex-shrink: 0; }
.air-quality-section { display: flex; align-items: center; gap: 12px; padding: 10px 16px; background: var(--bg-secondary); border-radius: 8px; }
.aqi-badge { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 700; color: #fff; }
.aqi-badge.good { background: var(--ws-success); }
.aqi-badge.moderate { background: var(--ws-warning); }
.aqi-badge.unhealthy-sensitive { background: #ff5722; }
.aqi-badge.unhealthy { background: #f44336; }
.aqi-badge.very-unhealthy { background: #9c27b0; }
.aqi-info { display: flex; flex-direction: column; gap: 2px; }
.aqi-label { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.aqi-detail { font-size: 11px; color: var(--text-tertiary); }
.hourly-section { padding: 16px; background: var(--bg-secondary); border-radius: 12px; }
.section-title { font-size: 13px; color: var(--text-tertiary); margin: 0 0 12px; text-transform: uppercase; letter-spacing: 0.5px; }
.hourly-scroll { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 4px; }
.hourly-item { display: flex; flex-direction: column; align-items: center; gap: 4px; min-width: 52px; padding: 8px 4px; background: var(--bg-secondary); border-radius: 8px; }
.hourly-time { font-size: 11px; color: var(--text-tertiary); }
.hourly-icon { display: flex; align-items: center; justify-content: center; }
.hourly-icon :deep(svg) { width: 24px; height: 24px; }
.hourly-temp { font-size: 13px; color: var(--text-primary); font-weight: 500; }
.hourly-precip { font-size: 10px; color: var(--ws-info); }
.daily-section { padding: 16px; background: var(--bg-secondary); border-radius: 12px; }
.daily-list { display: flex; flex-direction: column; gap: 6px; }
.daily-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; background: var(--bg-secondary); border-radius: 8px; }
.daily-day { font-size: 13px; color: var(--text-primary); min-width: 60px; }
.daily-icon { display: flex; align-items: center; }
.daily-icon :deep(svg) { width: 24px; height: 24px; }
.daily-label { font-size: 12px; color: #999; min-width: 50px; }
.daily-temp-bar { display: flex; align-items: center; gap: 6px; flex: 1; }
.daily-min { font-size: 12px; color: var(--ws-info); min-width: 30px; text-align: right; }
.daily-max { font-size: 12px; color: #ff8a65; min-width: 30px; }
.temp-bar { flex: 1; height: 4px; background: var(--border-color); border-radius: 2px; position: relative; }
.temp-bar-fill { position: absolute; top: 0; height: 100%; background: linear-gradient(90deg, var(--ws-info), #ff8a65); border-radius: 2px; }
.daily-extras { display: flex; gap: 8px; min-width: 80px; justify-content: flex-end; }
.daily-precip { font-size: 11px; color: var(--ws-info); }
.daily-wind { font-size: 11px; color: var(--text-tertiary); }
.sun-section { display: flex; gap: 20px; padding: 12px 16px; background: var(--bg-secondary); border-radius: 12px; }
.sun-info { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #ccc; }
.weather-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; padding: 64px; color: var(--text-tertiary); }
.weather-empty svg { color: #333; }
.ai-panel { width: 320px; border-left: 1px solid var(--border-color); background: var(--bg-secondary); display: flex; flex-direction: column; overflow: hidden; }
.ai-panel-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border-bottom: 1px solid var(--border-color); }
.ai-panel-header h4 { margin: 0; font-size: 14px; color: var(--ws-accent-soft); }
.close-btn { background: none; border: none; color: var(--text-tertiary); cursor: pointer; }
.close-btn:hover { color: #fff; }
.ai-panel-content { flex: 1; overflow-y: auto; padding: 12px; }
.ai-loading { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 24px; color: var(--text-tertiary); }
.ai-result { color: var(--text-primary); }
.ai-section { margin-bottom: 16px; }
.ai-section h5 { font-size: 12px; color: var(--text-tertiary); margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.5px; }
.outfit-card { padding: 10px; background: var(--bg-secondary); border-radius: 8px; }
.outfit-item { padding: 4px 0; font-size: 13px; color: var(--text-secondary); }
.outfit-label { color: var(--ws-accent); font-weight: 600; margin-right: 4px; }
.outfit-tip { margin-top: 8px; padding: 6px 8px; background: var(--border-color); border-radius: 4px; font-size: 12px; color: var(--ws-accent-soft); }
.advice-text { font-size: 13px; line-height: 1.6; color: var(--text-secondary); padding: 8px; background: var(--bg-secondary); border-radius: 6px; }
.precautions { margin-top: 8px; }
.precautions h6 { font-size: 11px; color: var(--text-tertiary); margin: 0 0 4px; }
.precaution-item { font-size: 12px; color: var(--ws-warning); padding: 4px 8px; background: var(--bg-secondary); border-radius: 4px; margin-bottom: 3px; }
.best-time { margin-top: 8px; font-size: 12px; color: var(--ws-success); }
.transport-tips { margin-top: 4px; font-size: 12px; color: var(--ws-info); }
.adjustment-item { padding: 8px; background: var(--bg-secondary); border-radius: 6px; margin-bottom: 6px; }
.adj-original { font-size: 12px; color: #ff8a65; text-decoration: line-through; }
.adjustment-item svg { color: var(--ws-accent); margin: 4px 0; }
.adj-suggested { font-size: 13px; color: var(--ws-success); }
.adj-reason { font-size: 11px; color: var(--text-tertiary); margin-top: 4px; }
.indoor-alt { margin-top: 8px; }
.indoor-alt h6 { font-size: 11px; color: var(--text-tertiary); margin: 0 0 4px; }
.alt-item { font-size: 12px; color: var(--text-secondary); padding: 4px 8px; background: var(--bg-secondary); border-radius: 4px; margin-bottom: 3px; }
.health-tip { padding: 6px 8px; background: var(--bg-secondary); border-radius: 4px; margin-bottom: 4px; font-size: 12px; display: flex; gap: 6px; align-items: baseline; }
.tip-category { color: var(--ws-accent); font-weight: 600; white-space: nowrap; }
.tip-advice { color: var(--text-secondary); }
.health-tip.priority-high { border-left: 3px solid #f44336; }
.health-tip.priority-medium { border-left: 3px solid var(--ws-warning); }
.health-tip.priority-low { border-left: 3px solid var(--ws-success); }
.warnings { margin-top: 8px; }
.warning-item { font-size: 12px; color: #f44336; padding: 4px 8px; background: #2a1a1a; border-radius: 4px; margin-bottom: 3px; }
.ai-empty { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-tertiary); font-size: 13px; text-align: center; padding: 16px; }
</style>
