/**
 * Turn FastAPI / axios errors into a single user-facing string.
 */
export function formatApiError(err) {
  if (!err || typeof err !== 'object') return String(err)
  if (!err.response) return err.message || 'Network error'
  const data = err.response.data
  const d = data && data.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) {
    return d
      .map((x) => {
        if (typeof x === 'object' && x !== null && x.msg) return x.msg
        return JSON.stringify(x)
      })
      .join('; ')
  }
  if (d && typeof d === 'object') return JSON.stringify(d)
  const code = err.response.status
  return err.message || `Request failed (${code})`
}
