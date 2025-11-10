type ClassValue = string | null | undefined | false | ClassValue[];

function flattenClasses(value: ClassValue): string[] {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value.flatMap((item) => flattenClasses(item));
  }
  return [value];
}

export function cn(...inputs: ClassValue[]): string {
  return inputs.flatMap((value) => flattenClasses(value)).join(" ");
}
