const timeFormatter = new Intl.DateTimeFormat("en-US", {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: true,
});

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

function parseDate(value?: string | number | Date): Date | null {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return date;
}

export function formatLocalTime(value?: string | number | Date): string {
  const date = parseDate(value);
  if (!date) {
    return value === null || value === undefined || value === "" ? "n/a" : String(value);
  }
  return timeFormatter.format(date);
}

export function formatLocalDateTime(value?: string | number | Date): string {
  const date = parseDate(value);
  if (!date) {
    return value === null || value === undefined || value === "" ? "n/a" : String(value);
  }

  const localDate = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  return `${localDate} ${formatLocalTime(date)}`;
}
