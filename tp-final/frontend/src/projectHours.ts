export type HoursProject = { fecha_inicio: string | null; fecha_fin: string | null; horas_requeridas: number }
export type HoursConsumption = { fecha_inicio: string; fecha_fin: string; horas_consumidas: number }
export type HoursTask = { fecha_inicio: string; fecha_fin: string; horas_requeridas: number }
export type HoursPoint = { date: string; planned: number; actual: number }
export function reportToday() {
  const parts = new Intl.DateTimeFormat('en', { timeZone: 'America/Argentina/Buenos_Aires', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date())
  const part = (type: string) => parts.find(value => value.type === type)!.value
  return `${part('year')}-${part('month')}-${part('day')}`
}
const DAY = 86400000
const dayNumber = (date: string) => Date.parse(date) / DAY

/** Inclusive calendar dates in UTC; each consumption is distributed evenly across its period. */
export function projectHours(project: HoursProject, consumptions: HoursConsumption[], tasks: HoursTask[] = [], through?: string): HoursPoint[] {
  if (!project.fecha_inicio || !project.fecha_fin) return []
  const start = dayNumber(project.fecha_inicio)
  const finish = dayNumber(project.fecha_fin)
  let end = through ? Math.max(finish, dayNumber(through)) : finish
  const changes = new Map<number, number>()
  const add = (day: number, value: number) => changes.set(day, (changes.get(day) ?? 0) + value)
  let actual = 0
  for (const consumption of consumptions) {
    const from = dayNumber(consumption.fecha_inicio)
    const to = dayNumber(consumption.fecha_fin)
    const daily = consumption.horas_consumidas / (to - from + 1)
    end = Math.max(end, to)
    // Include any hours prior to the project in the first visible accumulated balance.
    actual += Math.max(0, Math.min(to + 1, start) - from) * daily
    if (to >= start) {
      add(Math.max(start, from), daily)
      add(to + 1, -daily)
    }
  }
  const planChanges = new Map<number, number>()
  for (const task of tasks) {
    const from = dayNumber(task.fecha_inicio), to = dayNumber(task.fecha_fin)
    const daily = task.horas_requeridas / (to - from + 1)
    planChanges.set(from, (planChanges.get(from) ?? 0) + daily)
    planChanges.set(to + 1, (planChanges.get(to + 1) ?? 0) - daily)
  }
  let planned = 0, plannedRate = 0
  const points: HoursPoint[] = []
  let rate = 0
  for (let day = start; day <= end; day++) {
    plannedRate += planChanges.get(day) ?? 0
    planned += plannedRate
    rate += changes.get(day) ?? 0
    actual += rate
    points.push({
      date: new Date(day * DAY).toISOString().slice(0, 10),
      planned: day >= finish ? tasks.reduce((sum, task) => sum + task.horas_requeridas, 0) : Math.max(0, planned),
      actual: Math.max(0, actual),
    })
  }
  return points
}


type Trend = { slope: number; last: number; count: number }

/** OLS slope over observed daily cumulative totals, anchored to the last actual balance. */
function trend(points: HoursPoint[], lastDate: string): Trend | null {
  const observed = points.filter(point => point.date <= lastDate)
  if (!lastDate || observed.length < 2) return null
  const count = observed.length
  const meanX = (count - 1) / 2
  const meanY = observed.reduce((sum, point) => sum + point.actual, 0) / count
  let covariance = 0
  let variance = 0
  observed.forEach((point, index) => {
    covariance += (index - meanX) * (point.actual - meanY)
    variance += (index - meanX) ** 2
  })
  return { slope: covariance / variance, last: observed[count - 1]!.actual, count }
}

const lastConsumptionDate = (consumptions: HoursConsumption[]) =>
  consumptions.reduce((last, row) => row.fecha_fin > last ? row.fecha_fin : last, '')

export function projectForecast(points: HoursPoint[], consumptions: HoursConsumption[], finish: string | null, reportDate = reportToday()) {
  const lastDate = lastConsumptionDate(consumptions)
  const startDate = reportDate > lastDate ? reportDate : lastDate
  const values: (number | null)[] = points.map(() => null)
  const fit = trend(points, lastDate)
  if (!fit || !finish || startDate >= finish) return { lastDate, startDate, values, slope: fit?.slope ?? null }
  for (let index = fit.count - 1; index < points.length; index++) {
    const day = points[index]!.date
    if (day >= startDate && day <= finish) values[index] = fit.last + fit.slope * (dayNumber(day) - dayNumber(startDate))
  }
  return { lastDate, startDate, values, slope: fit.slope }
}

export type ForecastStatus = { text: string; acceptable: boolean }

/** Projected hours at the planned end against the required ones (±15 %). */
export function forecastStatus(projected: number | null, required: number): ForecastStatus | null {
  if (projected === null || required <= 0) return null
  const ratio = projected / required
  // Tolerance only compensates floating-point noise at the inclusive boundaries.
  if (ratio > 1.15 + 1e-12) return { text: 'Sobre aplicacion', acceptable: false }
  if (ratio < 0.85 - 1e-12) return { text: 'Falta de Recursos', acceptable: false }
  return { text: 'Aceptable', acceptable: true }
}

const addDays = (date: string, days: number) => new Date(Date.parse(date) + days * DAY).toISOString().slice(0, 10)

/**
 * Day on which the cumulative hours reach `required`: the first real day if they already did,
 * otherwise the regression line starting at the report date (also for overdue projects).
 * Null when there is no usable trend (fewer than 2 days of data, or a flat/negative slope).
 */
export function projectedEndDate(points: HoursPoint[], consumptions: HoursConsumption[], required: number, reportDate = reportToday()) {
  if (required <= 0) return null
  const reached = points.find(point => point.actual >= required - 1e-9)
  if (reached) return reached.date
  const lastDate = lastConsumptionDate(consumptions)
  const fit = trend(points, lastDate)
  if (!fit || fit.slope <= 0) return null
  return addDays(reportDate > lastDate ? reportDate : lastDate, Math.ceil((required - fit.last) / fit.slope - 1e-9))
}
