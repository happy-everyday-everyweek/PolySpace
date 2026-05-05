import { ref } from 'vue'

const DB_NAME = 'polyspace_docs'
const DB_VERSION = 1

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION)
    req.onupgradeneeded = () => {
      const db = req.result
      if (!db.objectStoreNames.contains('documents')) {
        db.createObjectStore('documents', { keyPath: 'id' })
      }
      if (!db.objectStoreNames.contains('versions')) {
        const store = db.createObjectStore('versions', { keyPath: 'id' })
        store.createIndex('docId', 'docId', { unique: false })
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

export function useDocumentPersistence(storeName: string) {
  const saveStatus = ref<'saved' | 'unsaved' | 'saving'>('saved')

  async function saveDoc(docId: string, data: Record<string, any>): Promise<void> {
    try {
      const db = await openDB()
      const tx = db.transaction('documents', 'readwrite')
      const store = tx.objectStore('documents')
      const serializable = JSON.parse(JSON.stringify(data))
      store.put({ id: `${storeName}_${docId}`, ...serializable, storeName, updatedAt: Date.now() })
      await new Promise<void>((resolve, reject) => {
        tx.oncomplete = () => resolve()
        tx.onerror = () => reject(tx.error)
      })
    } catch (e) {
      console.error('Failed to save document:', e)
    }
  }

  async function loadDoc(docId: string): Promise<Record<string, any> | null> {
    try {
      const db = await openDB()
      const tx = db.transaction('documents', 'readonly')
      const store = tx.objectStore('documents')
      const req = store.get(`${storeName}_${docId}`)
      return new Promise((resolve) => {
        req.onsuccess = () => resolve(req.result || null)
        req.onerror = () => resolve(null)
      })
    } catch {
      return null
    }
  }

  async function loadAllDocs(): Promise<Record<string, any>[]> {
    try {
      const db = await openDB()
      const tx = db.transaction('documents', 'readonly')
      const store = tx.objectStore('documents')
      const req = store.getAll()
      return new Promise((resolve) => {
        req.onsuccess = () => {
          const all = req.result || []
          resolve(all.filter((d: any) => d.storeName === storeName))
        }
        req.onerror = () => resolve([])
      })
    } catch {
      return []
    }
  }

  async function deleteDoc(docId: string): Promise<void> {
    try {
      const db = await openDB()
      const tx = db.transaction('documents', 'readwrite')
      const store = tx.objectStore('documents')
      store.delete(`${storeName}_${docId}`)
      await new Promise<void>((resolve, reject) => {
        tx.oncomplete = () => resolve()
        tx.onerror = () => reject(tx.error)
      })
    } catch (e) {
      console.error('Failed to delete document:', e)
    }
  }

  async function saveVersion(docId: string, content: string, label?: string): Promise<void> {
    try {
      const db = await openDB()
      const tx = db.transaction('versions', 'readwrite')
      const store = tx.objectStore('versions')
      store.put({
        id: `${storeName}_${docId}_${Date.now()}`,
        docId: `${storeName}_${docId}`,
        content,
        label: label || 'auto',
        createdAt: Date.now(),
      })
      await new Promise<void>((resolve, reject) => {
        tx.oncomplete = () => resolve()
        tx.onerror = () => reject(tx.error)
      })
    } catch (e) {
      console.error('Failed to save version:', e)
    }
  }

  async function getVersions(docId: string): Promise<Record<string, any>[]> {
    try {
      const db = await openDB()
      const tx = db.transaction('versions', 'readonly')
      const store = tx.objectStore('versions')
      const index = store.index('docId')
      const req = index.getAll(`${storeName}_${docId}`)
      return new Promise((resolve) => {
        req.onsuccess = () => resolve((req.result || []).sort((a: any, b: any) => b.createdAt - a.createdAt))
        req.onerror = () => resolve([])
      })
    } catch {
      return []
    }
  }

  return {
    saveStatus,
    saveDoc,
    loadDoc,
    loadAllDocs,
    deleteDoc,
    saveVersion,
    getVersions,
  }
}
