const numberFormat = new Intl.NumberFormat('es-AR', { maximumFractionDigits: 2 })

export const fmt = (value: number | null | undefined) => numberFormat.format(value ?? 0)

export const statusClass = (status: string) => 'status status-' + status.replaceAll(' ', '-')

/** Form inputs hold strings; an empty field becomes NaN (sent as null) so the API rejects it. */
export const toNumber = (value: string | number | null | undefined) =>
  value === '' || value === null || value === undefined ? Number.NaN : Number(value)

export const toText = (value: string | number | null | undefined) =>
  value === null || value === undefined ? '' : String(value)
